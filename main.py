from fastapi import FastAPI, Form
from twilio.twiml.messaging_response import MessagingResponse
from models.bedrock_client import chat_with_bedrock, extract_text
from models.twilio_client import send_whatsapp_message

app = FastAPI(title="Twilio WhatsApp + Bedrock AI Demo")

import requests

@app.post("/whatsapp")
async def whatsapp_webhook(From: str = Form(...), Body: str = Form(...)):
    print(f"✅ Received message from {From}: {Body}")

    try:
        resp = requests.post(
            "http://localhost:8001/mcp/query",
            json={"query": Body}
        )
        resp.raise_for_status()
        mcp_reply = resp.json()
        ai_reply = mcp_reply.get("message", "Sorry, I couldn’t process that.")

        # Example: hardcoded link for now
        payment_url = "http://localhost:8000/summons/8/payment-link"

        # Append to AI reply
        ai_reply += f"\n\n👉 Pay here: {payment_url}"

    except Exception as e:
        print("❌ Error calling MCP:", e)
        ai_reply = "Sorry, I couldn’t process that."

    # ✅ Send reply back via WhatsApp REST API
    send_whatsapp_message(From, ai_reply)

    # Optionally still return TwiML (not required if sending proactively)
    twiml_resp = MessagingResponse()
    twiml_resp.message(ai_reply)
    return str(twiml_resp)




