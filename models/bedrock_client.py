import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Init session and client
session = boto3.Session(profile_name=os.getenv("AWS_PROFILE"))
client = session.client("bedrock-runtime", region_name=os.getenv("AWS_REGION"))

def chat_with_bedrock(
    messages,
    model_id="amazon.nova-pro-v1:0",
    max_tokens=256,
    temperature=0.2,
    top_p=0.9,
):
    """
    Call Amazon Nova with chat-style messages.
    """
    payload = {
        "messages": messages,
        "system": [{"text": "You are a helpful assistant."}],
        "inferenceConfig": {
            "maxTokens": max_tokens,
            "temperature": temperature,
            "topP": top_p,
        }
    }

    resp = client.invoke_model(
        modelId=model_id,
        body=json.dumps(payload),
        contentType="application/json",
        accept="application/json",
    )

    return json.loads(resp["body"].read())


def extract_text(response):
    """
    Extract the assistant's reply text from Nova response.
    """
    try:
        # Nova replies are in response["output"]["message"]["content"]
        contents = response["output"]["message"]["content"]
        texts = [c.get("text") for c in contents if c.get("text")]
        return "\n".join(texts) if texts else None
    except Exception:
        return None
