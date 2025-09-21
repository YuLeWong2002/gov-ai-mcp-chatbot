"""
MCP Server (local) - FastAPI

Features:
- Simple intent routing (keyword + regex based)
- Calls your existing JPJ API Gateway endpoints
- Formats responses for a chatbot
- Run locally with: uvicorn mcp_server:app --reload --port 8080

Environment variables:
- JPJ_BASE_URL - base URL for your JPJ API (default uses the provided Lambda URL)

Endpoints:
- POST /mcp/query  -> {"query": "Check summons for W 1234 A"}

Notes:
- Production: replace simple intent detection with an LLM classifier or more robust NLU.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import re
import requests
from datetime import datetime

JPJ_BASE_URL = os.getenv("JPJ_BASE_URL", "https://dl7y68bl5l.execute-api.ap-southeast-5.amazonaws.com/default/jpj/")

app = FastAPI(title="MCP Local Router", version="0.1")

# --- request/response models ---
class MCPRequest(BaseModel):
    query: str
    vehicle_id: Optional[str] = None
    ic_number: Optional[str] = None

class MCPResponse(BaseModel):
    tool: str
    raw: Any
    message: str

# --- simple intent router ---
def detect_intent(query: str) -> Dict[str, str]:
    q = query.lower()

    # direct vehicle id pattern (letters/numbers/spaces/dashes)
    vid_match = re.search(r"([A-Z]{1,3}\s?\d{1,4}\s?[A-Z]{0,3})", query.upper())

    # keywords
    if any(k in q for k in ["summon", "summons", "ticket", "fines", "fine"]):
        intent = "get_summons"
    elif any(k in q for k in ["license", "renew", "expiry", "expire", "road tax"]):
        intent = "get_license"
    elif any(k in q for k in ["stats", "summary", "report"]):
        intent = "get_stats"
    else:
        # fallback to checking if they provided vehicle id
        if vid_match:
            intent = "get_summons"
        else:
            intent = "unknown"

    return {
        "intent": intent,
        "vehicle_id_guess": vid_match.group(1).strip() if vid_match else None
    }

# --- helpers to call JPJ API ---

def call_get_summons(vehicle_id: str):
    url = f"{JPJ_BASE_URL}summons/{vehicle_id}"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 200:
        return resp.json()
    elif resp.status_code == 404:
        return []
    else:
        raise HTTPException(status_code=502, detail=f"JPJ API error: {resp.status_code} {resp.text}")


def call_get_license(vehicle_id: str):
    url = f"{JPJ_BASE_URL}licenses/{vehicle_id}"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 200:
        return resp.json()
    elif resp.status_code == 404:
        return None
    else:
        raise HTTPException(status_code=502, detail=f"JPJ API error: {resp.status_code} {resp.text}")


def call_get_stats():
    url = f"{JPJ_BASE_URL}stats/summary"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 200:
        return resp.json()
    else:
        raise HTTPException(status_code=502, detail=f"JPJ API error: {resp.status_code} {resp.text}")

# --- formatting ---

def format_summons_list(summons: List[Dict[str, Any]]) -> str:
    if not summons:
        return "No summons found for this vehicle."
    lines = []
    for s in summons:
        d = s.get("summons_date") or s.get("summons_date")
        amt = s.get("amount")
        typ = s.get("summons_type")
        status = s.get("status")
        lines.append(f"{typ} on {d} — RM {amt} ({status})")
    return "\n".join(lines)


def format_license(lic: Dict[str, Any]) -> str:
    if not lic:
        return "No license record found for this vehicle."
    return (
        f"Owner: {lic.get('owner_name')}\n"
        f"Vehicle: {lic.get('vehicle_id')}\n"
        f"IC: {lic.get('ic_number')}\n"
        f"Expiry: {lic.get('expiry_date')}\n"
        f"Renewal fee: RM {lic.get('renewal_fee')}"
    )

# --- main MCP endpoint ---
@app.post("/mcp/query", response_model=MCPResponse)
async def mcp_query(payload: MCPRequest):
    q = payload.query.strip()
    route = detect_intent(q)
    intent = route['intent']

    # if user provided explicit vehicle_id or ic, prefer that
    vehicle_id = payload.vehicle_id or payload.ic_number or route['vehicle_id_guess']

    if intent == 'get_summons':
        if not vehicle_id:
            raise HTTPException(status_code=400, detail="Vehicle ID not found in query or payload.")
        raw = call_get_summons(vehicle_id)
        message = format_summons_list(raw)
        return MCPResponse(tool='get_summons', raw=raw, message=message)

    if intent == 'get_license':
        if not vehicle_id:
            raise HTTPException(status_code=400, detail="Vehicle ID not found in query or payload.")
        raw = call_get_license(vehicle_id)
        message = format_license(raw)
        return MCPResponse(tool='get_license', raw=raw, message=message)

    if intent == 'get_stats':
        raw = call_get_stats()
        # small formatting
        message = (
            f"Total licenses: {raw.get('total_licenses')}\n"
            f"Total summons: {raw.get('total_summons')}\n"
            f"Unpaid summons: {raw.get('unpaid_summons')} (RM {raw.get('unpaid_amount')})\n"
            f"Expired licenses: {raw.get('expired_licenses')}")
        return MCPResponse(tool='get_stats', raw=raw, message=message)

    # fallback behaviour: echo and suggest options
    return MCPResponse(tool='none', raw=None, message=(
        "Sorry, I couldn't figure out what you want. Try: 'Check summons for <VEHICLE_ID>' or 'Show license for <VEHICLE_ID>' or 'Get stats'."
    ))


# --- simple healthcheck ---
@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
