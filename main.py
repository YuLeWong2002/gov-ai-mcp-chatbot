from fastapi import FastAPI, Form
from twilio.twiml.messaging_response import MessagingResponse
from model.bedrock_client import chat_with_bedrock, extract_text
from model.twilio_client import send_whatsapp_message

app = FastAPI(title="Twilio WhatsApp + Bedrock AI Demo")

@app.post("/whatsapp")
async def whatsapp_webhook(From: str = Form(...), Body: str = Form(...)):
    print(f"✅ Received message from {From}: {Body}")

    messages = [{"role": "user", "content": [{"text": Body}]}]

    try:
        response = chat_with_bedrock(messages)
        print("📥 Raw Bedrock response:", response)
        ai_reply = extract_text(response)
        print("🤖 Extracted AI reply:", ai_reply)
    except Exception as e:
        print("❌ Error calling Bedrock:", e)
        ai_reply = "Sorry, I couldn’t process that."

    twiml_resp = MessagingResponse()
    twiml_resp.message(ai_reply or "No reply from Bedrock")
    return str(twiml_resp)


