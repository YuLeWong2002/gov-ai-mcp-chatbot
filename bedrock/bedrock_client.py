import boto3
import json

session = boto3.Session(profile_name="awsisb_IsbUsersPS")  # 👈 Use your SSO profile

client = session.client("bedrock-runtime", region_name="us-east-1")


def chat_with_bedrock(
    messages,
    model_id="amazon.nova-pro-v1:0",
    max_tokens=256,
    temperature=0.2,
    top_p=0.9,
):
    """
    Send a chat request to Bedrock's conversational model.

    Args:
        messages (list): List of chat messages in Anthropic-like format:
            [{"role": "user", "content": [{"text": "Hello"}]}]
        model_id (str): Model ID, e.g., "amazon.nova-pro-v1:0"
        max_tokens (int): Max output tokens
        temperature (float): Sampling temperature
        top_p (float): Nucleus sampling

    Returns:
        dict: Raw JSON response from Bedrock
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
        body=json.dumps(payload).encode("utf-8"),
        contentType="application/json",
        accept="application/json",
    )

    # Parse response
    out = json.loads(resp["body"].read())
    return out


def extract_text(response):
    """
    Convenience function to extract plain text from Bedrock response.
    """
    try:
        return response["output"]["message"]["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return None
    
# Testing  
if __name__ == "__main__":
    # Example conversation
    messages = [
        {
            "role": "user",
            "content": [
                {"text": "Hello Bedrock! Can you summarize what AWS Bedrock does?"}
            ]
        }
    ]

    system_prompt = [{"text": "You are a helpful assistant."}]

    response = chat_with_bedrock(messages, model_id="amazon.nova-pro-v1:0")

    from bedrock_client import chat_with_bedrock, extract_text

    response = chat_with_bedrock(messages)
    print("=== Full Raw Response ===")
    print(response)

    print("\n=== Extracted Text ===")
    print(extract_text(response))

