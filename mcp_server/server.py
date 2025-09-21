from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import re
import requests
from datetime import datetime
from models.bedrock_client import chat_with_bedrock, extract_text
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Show debug and above
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

import stripe

stripe.api_key = os.getenv("sk_test_51S9LBMBt12OZb6sY4oAUWpfT5bBZuc8dch1Vi3VUEM4VkJcKGE0RAGchhXsJrWnXGLefs5tE2MPUo0UmgzVMPzA400Hp9jlVXU")

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
    print("Enter intent", flush=True)
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
    print("Enter intent", flush=True)
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

import requests

def format_summons_list(summons: List[Dict[str, Any]]) -> str:
    if not summons:
        return "No summons found for this vehicle."

    lines = []
    for s in summons:
        d = s.get("summons_date")
        amt = s.get("amount")
        typ = s.get("summons_type")
        status = s.get("status")
        summons_id = s.get("summons_id")

        if status and status.lower() == "unpaid":
            try:
                logger.debug(f"🔗 Generating Stripe link for summons {summons_id} (amount RM {amt})")
                result = create_payment_link(str(summons_id), float(amt))
                payment_url = result["payment_url"]
            except Exception as e:
                logger.error(f"❌ Error creating payment link: {e}")
                payment_url = "(payment link unavailable)"

            lines.append(f"{typ} on {d} — RM {amt} ({status})\n👉 [Pay here]({payment_url})")



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
    logger.debug(f"Incoming request payload = {payload.dict()}")

    q = payload.query.strip()
    logger.debug(f"Cleaned query = '{q}'")

    route = detect_intent(q)
    logger.debug(f"Intent detection result = {route}")

    intent = route['intent']
    vehicle_id = payload.vehicle_id or payload.ic_number or route['vehicle_id_guess']
    logger.debug(f"Final vehicle_id resolved = {vehicle_id}")

    if intent == 'get_summons':
        if not vehicle_id:
            logger.debug("No vehicle_id provided for summons intent")
            raise HTTPException(status_code=400, detail="Vehicle ID not found in query or payload.")

        logger.debug(f"Calling JPJ API get_summons for vehicle {vehicle_id}")
        raw = call_get_summons(vehicle_id)
        logger.debug(f"Raw summons API response = {raw}")

        context = format_summons_list(raw)
        logger.debug(f"Formatted summons context = {context}")

        messages = [
            {
                "role": "user",
                "content": [
                    {"text": "You are a JPJ assistant. Always answer based ONLY on the provided JPJ API result. Never say you lack access."}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"text": f"""
        The user asked: "{q}"

        Here is the JPJ API result for vehicle {vehicle_id}:
        {context}

        👉 Important rules:
        - Do NOT remove or rewrite the payment link Markdown (e.g., [Pay here](...)).
        - You may rephrase text for clarity, but links must be preserved exactly.
        - If no summons exist, just say so.
        Please answer naturally using ONLY this data.
        """}
                ]
            }
        ]


        logger.debug(f"Messages prepared for Bedrock = {messages}")

        bedrock_resp = chat_with_bedrock(messages)
        logger.debug(f"Raw Bedrock response = {bedrock_resp}")

        ai_reply = extract_text(bedrock_resp) or context
        logger.debug(f"Extracted AI reply = {ai_reply}")

        return MCPResponse(tool='get_summons', raw=raw, message=ai_reply)

        
    elif intent == 'get_license':
        if not vehicle_id:
            logger.debug("No vehicle_id provided for license intent")
            raise HTTPException(status_code=400, detail="Vehicle ID not found in query or payload.")

        logger.debug(f"Calling JPJ API get_license for vehicle {vehicle_id}")
        raw = call_get_license(vehicle_id)
        logger.debug(f"Raw license API response = {raw}")

        context = format_license(raw)
        logger.debug(f"Formatted license context = {context}")

        messages = [
            {
                "role": "user",
                "content": [
                    {"text": "You are a JPJ assistant. Always answer based ONLY on the provided JPJ API result. Never say you lack access."}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"text": f"""
    The user asked: "{q}"

    Here is the JPJ API result for vehicle {vehicle_id}:
    {context}

    👉 Please answer the user’s question clearly using ONLY this data. Important: Preserve the exact payment link markdown ([Pay here](...)) in your answer.
Please answer naturally, but never remove or rewrite the link.
    """}
                ]
            }
        ]

        logger.debug(f"Messages prepared for Bedrock = {messages}")
        bedrock_resp = chat_with_bedrock(messages)
        logger.debug(f"Raw Bedrock response = {bedrock_resp}")

        ai_reply = extract_text(bedrock_resp) or context
        logger.debug(f"Extracted AI reply = {ai_reply}")

        return MCPResponse(tool='get_license', raw=raw, message=ai_reply)
    elif intent == 'get_stats':
        logger.debug("Calling JPJ API get_stats")
        raw = call_get_stats()
        logger.debug(f"Raw stats API response = {raw}")

        context = f"JPJ statistics summary:\n{raw}"
        logger.debug(f"Formatted stats context = {context}")

        messages = [
            {
                "role": "user",
                "content": [
                    {"text": "You are a JPJ assistant. Always answer based ONLY on the provided JPJ API result. Never say you lack access."}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"text": f"""
    The user asked: "{q}"

    Here is the JPJ API stats summary:
    {context}

    👉 Please answer the user’s question clearly using ONLY this data.
    """}
                ]
            }
        ]

        logger.debug(f"Messages prepared for Bedrock = {messages}")
        bedrock_resp = chat_with_bedrock(messages)
        logger.debug(f"Raw Bedrock response = {bedrock_resp}")

        ai_reply = extract_text(bedrock_resp) or context
        logger.debug(f"Extracted AI reply = {ai_reply}")
        # Ensure payment link(s) survive
        if "[Pay here]" in context and "[Pay here]" not in ai_reply:
            logger.debug("⚠️ Bedrock dropped the payment link, reinjecting it.")
            ai_reply += f"\n\n{context}"

        return MCPResponse(tool='get_stats', raw=raw, message=ai_reply)



    # fallback -> let Bedrock handle open-ended queries
    print("DEBUG: Entering fallback intent (Bedrock only)", flush=True)
    messages = [{"role": "user", "content": [{"text": q}]}]
    print(f"DEBUG: Messages prepared for Bedrock fallback = {messages}", flush=True)

    bedrock_resp = chat_with_bedrock(messages)
    print(f"DEBUG: Raw Bedrock response (fallback) = {bedrock_resp}", flush=True)

    ai_reply = extract_text(bedrock_resp) or "Sorry, I couldn't process that."
    return MCPResponse(tool=intent, raw=bedrock_resp, message=ai_reply)


# --- simple healthcheck ---
@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/summons/{summons_id}/payment-link")
# --- update create_payment_link to accept amount ---
def create_payment_link(summons_id: str, amount_rm: float = 50.0):
    try:
        amount_sen = int(amount_rm * 100)
        logger.debug(f"Creating Stripe session for summons {summons_id}, amount_sen={amount_sen}")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "myr",
                    "product_data": {"name": f"JPJ Summons {summons_id}"},
                    "unit_amount": amount_sen,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="http://localhost:8000/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:8000/cancel",
        )

        logger.debug(f"✅ Stripe session created: {session}")
        return {"summons_id": summons_id, "payment_url": session.url}

    except Exception as e:
        logger.error(f"❌ Stripe error: {e}", exc_info=True)
        return {"summons_id": summons_id, "payment_url": "(payment link unavailable)"}
    
def inject_payment_link(ai_reply: str, summons_id: str, amount: float = 250.0):
    # Call your Stripe helper
    payment_data = create_payment_link(summons_id, amount)
    payment_url = payment_data.get("payment_url", "(payment link unavailable)")

    # Replace placeholder if AI left one
    if "(payment link unavailable)" in ai_reply:
        return ai_reply.replace("(payment link unavailable)", payment_url)
    
    # Or append link at the end if missing
    if "Pay here" not in ai_reply and payment_url.startswith("http"):
        ai_reply += f"\n\n👉 [Pay here]({payment_url})"
    
    return ai_reply

