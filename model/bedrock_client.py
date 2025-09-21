import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

session = boto3.Session(profile_name=os.getenv("AWS_PROFILE"))
client = session.client("bedrock-runtime", region_name=os.getenv("AWS_REGION"))

def chat_with_bedrock(
    messages,
    model_id="amazon.nova-pro-v1:0",
    max_tokens=256,
    temperature=0.2,
    top_p=0.9,
):
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
        body=json.dumps(payload).encode("utf-8"),
        contentType="application/json",
        accept="application/json",
    )

    out = json.loads(resp["body"].read())
    return out

def extract_text(response):
    try:
        return response["output"]["message"]["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return None
