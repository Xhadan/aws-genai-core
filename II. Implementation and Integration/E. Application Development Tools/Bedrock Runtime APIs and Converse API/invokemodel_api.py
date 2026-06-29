import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime')

def invoke_claude(prompt: str, system: str = None) -> dict:
    """Invoke Claude model with Anthropic format."""

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "temperature": 0.7,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    if system:
        body["system"] = system

    response = bedrock_runtime.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response['body'].read())

    return {
        'text': result['content'][0]['text'],
        'input_tokens': result['usage']['input_tokens'],
        'output_tokens': result['usage']['output_tokens'],
        'stop_reason': result['stop_reason']
    }

def invoke_titan(prompt: str) -> dict:
    """Invoke Amazon Titan model."""

    body = {
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 1024,
            "temperature": 0.7,
            "topP": 0.9,
            "stopSequences": []
        }
    }

    response = bedrock_runtime.invoke_model(
        modelId="amazon.titan-text-express-v1",
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response['body'].read())

    return {
        'text': result['results'][0]['outputText'],
        'token_count': result['results'][0]['tokenCount'],
        'completion_reason': result['results'][0]['completionReason']
    }

def invoke_llama(prompt: str) -> dict:
    """Invoke Meta Llama model."""

    body = {
        "prompt": f"<s>[INST] {prompt} [/INST]",
        "max_gen_len": 1024,
        "temperature": 0.7,
        "top_p": 0.9
    }

    response = bedrock_runtime.invoke_model(
        modelId="meta.llama3-1-8b-instruct-v1:0",
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response['body'].read())

    return {
        'text': result['generation'],
        'prompt_token_count': result['prompt_token_count'],
        'generation_token_count': result['generation_token_count'],
        'stop_reason': result['stop_reason']
    }

def invoke_mistral(prompt: str) -> dict:
    """Invoke Mistral model."""

    body = {
        "prompt": f"<s>[INST] {prompt} [/INST]",
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.9
    }

    response = bedrock_runtime.invoke_model(
        modelId="mistral.mistral-7b-instruct-v0:2",
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response['body'].read())

    return {
        'text': result['outputs'][0]['text'],
        'stop_reason': result['outputs'][0]['stop_reason']
    }

# Usage
claude_result = invoke_claude("What is quantum computing?")
print(f"Claude: {claude_result['text'][:200]}...")

titan_result = invoke_titan("Explain machine learning.")
print(f"Titan: {titan_result['text'][:200]}...")