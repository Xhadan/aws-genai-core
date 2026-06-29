import boto3
from typing import List, Dict, Optional

bedrock_runtime = boto3.client('bedrock-runtime')

def converse(
    messages: List[Dict],
    model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
    system: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.7
) -> dict:
    """
    Use Converse API for unified conversation interface.
    Works with Claude, Titan, Llama, Mistral, etc.
    """

    # Build inference config
    inference_config = {
        "maxTokens": max_tokens,
        "temperature": temperature
    }

    # Build request
    request = {
        "modelId": model_id,
        "messages": messages,
        "inferenceConfig": inference_config
    }

    # Add system prompt if provided
    if system:
        request["system"] = [{"text": system}]

    response = bedrock_runtime.converse(**request)

    # Extract response
    output = response['output']['message']
    usage = response['usage']

    return {
        'role': output['role'],
        'content': output['content'][0]['text'],
        'input_tokens': usage['inputTokens'],
        'output_tokens': usage['outputTokens'],
        'stop_reason': response['stopReason']
    }

def converse_stream(
    messages: List[Dict],
    model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
    system: Optional[str] = None,
    max_tokens: int = 1024
):
    """
    Streaming Converse API.
    """

    request = {
        "modelId": model_id,
        "messages": messages,
        "inferenceConfig": {"maxTokens": max_tokens}
    }

    if system:
        request["system"] = [{"text": system}]

    response = bedrock_runtime.converse_stream(**request)

    for event in response['stream']:
        if 'contentBlockDelta' in event:
            delta = event['contentBlockDelta']['delta']
            if 'text' in delta:
                yield delta['text']

        elif 'messageStop' in event:
            break

        elif 'metadata' in event:
            usage = event['metadata'].get('usage', {})
            yield {
                'type': 'metadata',
                'input_tokens': usage.get('inputTokens'),
                'output_tokens': usage.get('outputTokens')
            }

def multi_turn_conversation(model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"):
    """Example multi-turn conversation using Converse API."""

    messages = []
    system = "You are a helpful AI assistant specializing in AWS services."

    # Turn 1
    messages.append({
        "role": "user",
        "content": [{"text": "What is Amazon S3?"}]
    })

    response = converse(messages, model_id, system)
    print(f"Assistant: {response['content']}\n")

    messages.append({
        "role": "assistant",
        "content": [{"text": response['content']}]
    })

    # Turn 2
    messages.append({
        "role": "user",
        "content": [{"text": "What are the storage classes?"}]
    })

    response = converse(messages, model_id, system)
    print(f"Assistant: {response['content']}\n")

    messages.append({
        "role": "assistant",
        "content": [{"text": response['content']}]
    })

    # Turn 3
    messages.append({
        "role": "user",
        "content": [{"text": "Which is most cost-effective for rarely accessed data?"}]
    })

    response = converse(messages, model_id, system)
    print(f"Assistant: {response['content']}\n")

    return messages

# Cross-model usage - same code works for different models
models_to_test = [
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "amazon.titan-text-express-v1",
    "meta.llama3-1-8b-instruct-v1:0"
]

messages = [{"role": "user", "content": [{"text": "What is cloud computing?"}]}]

for model in models_to_test:
    try:
        result = converse(messages, model_id=model)
        print(f"\n{model}:\n{result['content'][:200]}...")
    except Exception as e:
        print(f"\n{model}: Error - {e}")