import boto3

bedrock = boto3.client('bedrock-runtime')

def chat(user_message, history):
    """
    Every call includes the full conversation history.
    The model doesn't remember anything on its own.
    """
    messages = history + [{"role": "user", "content": user_message}]

    response = bedrock.converse(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        messages=messages,
        inferenceConfig={"maxTokens": 1024}
    )

    return response['output']['message']['content'][0]['text']

# History stored in DynamoDB, fetched per request
history = [
    {"role": "user", "content": "What is AWS?"},
    {"role": "assistant", "content": "AWS is Amazon Web Services..."}
]

# This call includes everything above
response = chat("Tell me about Bedrock", history)