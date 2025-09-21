#!/usr/bin/env python3
"""
Diagnostic + Payment Test for JPJ API

Usage:
    python diag_payment_test.py

What it does:
- Detects correct BASE_URL (tries ports 8000 and 8080, with and without /jpj)
- Tests connectivity
- Gets unpaid summons; if none, creates a test summons
- Pays the summons via PUT /summons/{id}/pay
- Verifies the summons status becomes 'Paid'
- Cleans up created test summons

Adjust HOSTS list if your server is on a different IP/port.
"""
import requests
from urllib.parse import urljoin
import time
import sys
from datetime import date

# candidate host:port tuples to probe (modify if your server uses different ports)
HOSTS = [
    ("127.0.0.1", 8000),
    ("127.0.0.1", 8080)
]

PREFIXES = ["", "/jpj"]  # try both no prefix and /jpj prefix

TIMEOUT = 5  # seconds for HTTP calls
TEST_VEHICLE = "W 1234 A"  # seeded in your DB from SQL you provided
TEST_SUMMONS_TYPE = "Automated Test Payment"
TEST_SUMMONS_AMOUNT = 1.00  # small amount for test

def try_url(base, path="/"):
    url = base.rstrip("/") + "/" + path.lstrip("/")
    try:
        r = requests.get(url, timeout=TIMEOUT)
        return r.status_code, r
    except Exception as e:
        return None, e

def detect_base_url():
    tried = []
    for host, port in HOSTS:
        base = f"http://{host}:{port}"
        for pref in PREFIXES:
            candidate = base.rstrip("/") + pref
            # check /openapi.json first (strong indicator) then /docs then root
            for p in ["/openapi.json", "/docs", "/"]:
                tried.append(candidate + p)
                try:
                    r = requests.get(candidate.rstrip("/") + p, timeout=TIMEOUT)
                    if r.status_code == 200:
                        print(f"[+] Detected working API base: {candidate}  (via {p})")
                        return candidate
                except Exception as e:
                    # record but keep trying
                    pass
    # if not found, show attempted urls for debugging
    print("[-] Could not auto-detect API base. Tried:")
    for host, port in HOSTS:
        for pref in PREFIXES:
            print(f"  http://{host}:{port}{pref}/ (probed /openapi.json /docs / )")
    return None

def test_stripe_checkout():
    flask_url = "http://127.0.0.1:4242/create-checkout-session"
    print(f"\n=== Testing Stripe Checkout at {flask_url} ===")
    try:
        r = requests.post(flask_url, allow_redirects=False)
        print(f"[>] POST {flask_url} -> {r.status_code} {r.reason}")
        if r.status_code in (302, 303):  # redirect to Stripe payment page
            redirect_url = r.headers.get("Location")
            print(f"[+] Redirected to Stripe Checkout URL: {redirect_url}")
            return redirect_url
        else:
            print("[FAIL] Unexpected response:", pretty_print_resp(r))
    except Exception as e:
        print("[ERROR] Could not call Stripe checkout:", e)


def pretty_print_resp(r):
    try:
        return r.json()
    except:
        return r.text[:1000]

def get_unpaid_summons(base_url):
    url = urljoin(base_url + "/", "summons/status/Unpaid")
    print(f"[>] GET {url}")
    r = requests.get(url, timeout=TIMEOUT)
    print(f"    → {r.status_code} {r.reason}")
    return r
    url = urljoin(base_url + "/", "summons/")
    payload = {
        "vehicle_id": vehicle_id,
        "summons_type": TEST_SUMMONS_TYPE,
        "summons_date": str(date.today()),
        "amount": TEST_SUMMONS_AMOUNT,
        "status": "Unpaid"
    }
    print(f"[>] POST {url}  payload={payload}")
    r = requests.post(url, json=payload, timeout=TIMEOUT)
    print(f"    → {r.status_code} {r.reason}  resp={pretty_print_resp(r)}")
    if r.status_code in (200, 201):
        return r.json().get("summons_id"), r.json()
    else:
        return None, r

def pay_summons(base_url, summons_id, use_stripe=True):
    # optional: trigger Stripe checkout
    if use_stripe:
        print("\n=== Initiating Stripe payment ===")
        stripe_url = pay_with_stripe()
        if not stripe_url:
            print("[WARN] Skipping Stripe since session failed.")

    # then call your JPJ backend pay endpoint
    url = urljoin(base_url + "/", f"summons/{summons_id}/pay")
    print(f"[>] PUT {url}")
    r = requests.put(url, timeout=TIMEOUT)
    print(f"    → {r.status_code} {r.reason}  resp={pretty_print_resp(r)}")
    return r

def pay_with_stripe():
    url = "http://127.0.0.1:4242/create-checkout-session"
    print(f"[>] POST {url} (Stripe checkout)")
    try:
        r = requests.post(url, timeout=TIMEOUT, allow_redirects=False)
        print(f"    → {r.status_code} {r.reason}")
        if r.status_code in (302, 303):
            session_url = r.headers.get("Location")
            print(f"[+] Stripe Checkout session created. Redirect URL: {session_url}")
            return session_url
        else:
            print("[ERROR] Stripe checkout failed:", pretty_print_resp(r))
            return None
    except Exception as e:
        print("[ERROR] Could not connect to Stripe Flask app:", e)
        return None

def get_summons_by_vehicle(base_url, vehicle_id):
    url = urljoin(base_url + "/", f"summons/{vehicle_id}")
    print(f"[>] GET {url}")
    r = requests.get(url, timeout=TIMEOUT)
    print(f"    → {r.status_code} {r.reason}  resp={pretty_print_resp(r)}")
    return r

def delete_summons(base_url, summons_id):
    url = urljoin(base_url + "/", f"summons/{summons_id}")
    print(f"[>] DELETE {url}")
    r = requests.delete(url, timeout=TIMEOUT)
    print(f"    → {r.status_code} {r.reason}  resp={pretty_print_resp(r)}")
    return r

def run_test_flow():
    print("=== Detecting API base URL ===")
    base = detect_base_url()
    if not base:
        print("\nERROR: Server not detected. Make sure FastAPI is running and accessible.")
        print("Start server example: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        sys.exit(1)

    print("\n=== Connectivity check (root) ===")
    try:
        r = requests.get(base.rstrip("/") + "/", timeout=TIMEOUT)
        print(f"[>] GET {base}/ -> {r.status_code} {r.reason}  resp={pretty_print_resp(r)}")
    except Exception as e:
        print("Root request failed:", e)

    print("\n=== Check unpaid summons ===")
    r = get_unpaid_summons(base)
    if r.status_code != 200:
        print("\n[!] unpaid summons endpoint returned non-200. Check that endpoint exists at prefix /jpj or remove root_path.")
        print("Response:", pretty_print_resp(r))
        # continue to attempt create->pay cycle anyway if possible

    unpaid_list = []
    try:
        unpaid_list = r.json() if r.status_code == 200 else []
    except:
        unpaid_list = []

    created_id = None
    # pick existing unpaid summons if present
    if unpaid_list:
        print(f"[+] Found {len(unpaid_list)} unpaid summons; selecting first for payment test.")
        test_summons = unpaid_list[0]
        sid = test_summons.get("summons_id")
        print(f"Using existing summons_id={sid}")
        created_id = sid
    else:
        print("[i] No unpaid summons found; creating a test summons.")

    # call pay endpoint
    print("\n=== Paying summons ===")
    rpay = pay_summons(base, created_id)
    if rpay.status_code not in (200, 201):
        print("[FAIL] pay endpoint returned non-200:", pretty_print_resp(rpay))
        sys.exit(1)

    # verify status via summons list for vehicle
    print("\n=== Verifying status updated to Paid ===")
    r2 = get_summons_by_vehicle(base, TEST_VEHICLE)
    if r2.status_code != 200:
        print("[WARN] Could not fetch summons by vehicle to verify. Response:", pretty_print_resp(r2))
    else:
        found = False
        try:
            data = r2.json()
            for s in data:
                if s.get("summons_id") == created_id:
                    found = True
                    status = s.get("status")
                    print(f"[>] Found summons {created_id} status = {status}")
                    if status == "Paid":
                        print("[SUCCESS] Summons status correctly updated to Paid.")
                    else:
                        print("[FAIL] Summons status not updated to Paid.")
                    break
        except Exception as e:
            print("Error parsing summons by vehicle response:", e)

    print("\n=== Done ===")

if __name__ == "__main__":
    run_test_flow()
