import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime')

def invoke_model_streaming(prompt: str, model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"):
    """
    Invoke Bedrock model with response streaming.
    Yields text chunks as they are generated.
    """
    response = bedrock_runtime.invoke_model_with_response_stream(
        modelId=model_id,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })
    )

    # Process streaming response
    for event in response['body']:
        chunk = json.loads(event['chunk']['bytes'])

        if chunk['type'] = 'content_block_delta':
            text = chunk['delta'].get('text', '')
            if text:
                yield text

        elif chunk['type'] = 'message_stop':
            # Stream complete
            break

# Usage: Display text progressively
print("Assistant: ", end="", flush=True)
for text_chunk in invoke_model_streaming("Explain quantum computing"):
    print(text_chunk, end="", flush=True)
print()  # Final newline