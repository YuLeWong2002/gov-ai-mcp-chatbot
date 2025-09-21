from fastapi import FastAPI, Form
from twilio.twiml.messaging_response import MessagingResponse
from model.bedrock_client import chat_with_bedrock, extract_text
from model.twilio_client import send_whatsapp_message

app = FastAPI(title="Twilio WhatsApp + Bedrock AI Demo")

@app.post("/whatsapp")
async def whatsapp_webhook(From: str = Form(...), Body: str = Form(...)):
    """
    Receive WhatsApp messages from Twilio sandbox, call Bedrock AI, reply.
    """
    print(f"Received message from {From}: {Body}")

    # Prepare Bedrock format
    messages = [{"role": "user", "content": [{"text": Body}]}]

    # Get AI response
    response = chat_with_bedrock(messages)
    ai_reply = extract_text(response) or "Sorry, I couldn't process that."

    # Send WhatsApp reply via Twilio
    send_whatsapp_message(to=From, body=ai_reply)

    # Twilio requires a 200 OK response; optional XML reply
    twiml_resp = MessagingResponse()
    twiml_resp.message("Message received and processed ✅")
    return str(twiml_resp)
