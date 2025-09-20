import requests
from datetime import date

BASE_URL = "http://127.0.0.1:8000"  # Change if your FastAPI server is deployed elsewhere

# ------------------------------
# Vehicle License Tests
# ------------------------------

def test_get_all_licenses():
    r = requests.get(f"{BASE_URL}/vehicle_licenses/")
    try:
        print("hi")
        data = r.json()
        print("bye")
    except Exception as e:
        print("Failed to decode JSON:", e)
        print("Raw response:", r.text)
    print("GET all licenses:", r.status, r.json()[:2])  # print first 2 for brevity

def test_get_license(vehicle_number):
    r = requests.get(f"{BASE_URL}/licenses/{vehicle_number}")
    print(f"GET license {vehicle_number}:", r.status, r.json())

def test_create_license():
    new_license = {
        "owner_name": "Test User",
        "ic_number": "990101-01-9999",
        "vehicle_number": "TEST123",
        "expiry_date": "2035-01-01",
        "renewal_fee": 100.0
    }
    r = requests.post(f"{BASE_URL}/vehicle_licenses/", json=new_license)
    print("POST create license:", r.status, r.json())
    return new_license["vehicle_number"]

def test_update_license(vehicle_number):
    updated_data = {
        "owner_name": "Test User Updated",
        "ic_number": "990101-01-9999",
        "vehicle_number": vehicle_number,
        "expiry_date": "2035-12-31",
        "renewal_fee": 150.0
    }
    r = requests.put(f"{BASE_URL}/vehicle_licenses/{vehicle_number}", json=updated_data)
    print("PUT update license:", r.status, r.json())

def test_delete_license(vehicle_number):
    r = requests.delete(f"{BASE_URL}/vehicle_licenses/{vehicle_number}")
    print("DELETE license:", r.status, r.json())

# ------------------------------
# Vehicle Summons Tests
# ------------------------------

def test_get_all_summons():
    r = requests.get(f"{BASE_URL}/vehicle_summons/")
    print("GET all summons:", r.status, r.json()[:2])  # first 2

def test_get_summons(summons_id):
    r = requests.get(f"{BASE_URL}/vehicle_summons/{summons_id}")
    print(f"GET summons {summons_id}:", r.status, r.json())

def test_create_summons():
    new_summons = {
        "vehicle_number": "TEST123",
        "ic_number": "990101-01-9999",
        "summons_type": "Speeding",
        "summons_date": str(date.today()),
        "amount": 200.0,
        "status": "Unpaid"
    }
    r = requests.post(f"{BASE_URL}/vehicle_summons/", json=new_summons)
    print("POST create summons:", r.status, r.json())
    return r.json()["summons_id"]  # <- changed from 'id' to 'summons_id'

def test_update_summons(summons_id):
    updated_summons = {
        "vehicle_number": "TEST123",
        "ic_number": "990101-01-9999",
        "summons_type": "Illegal Parking",
        "summons_date": str(date.today()),
        "amount": 250.0,
        "status": "Paid"
    }
    r = requests.put(f"{BASE_URL}/vehicle_summons/{summons_id}", json=updated_summons)
    print("PUT update summons:", r.status, r.json())

def test_delete_summons(summons_id):
    r = requests.delete(f"{BASE_URL}/vehicle_summons/{summons_id}")
    print("DELETE summons:", r.status, r.json())

# ------------------------------
# Run Tests
# ------------------------------
if __name__ == "__main__":
    # Vehicle License
    test_get_all_licenses()
    # test_get_license("W1001A")
    # vehicle_number = test_create_license()
    # test_update_license(vehicle_number)
    # test_delete_license(vehicle_number)

    # # Vehicle Summons
    # test_get_all_summons()
    # test_get_summons(1)
    # summons_id = test_create_summons()
    # test_update_summons(summons_id)
    # test_delete_summons(summons_id)
