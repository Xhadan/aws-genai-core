import boto3
import json
from typing import Optional, List, Dict, Any
from functools import lru_cache
from botocore.config import Config

class BedrockClient:
    """
    Production-ready Bedrock SDK client with best practices.
    """

    def __init__(
        self,
        region: str = "us-east-1",
        default_model: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    ):
        self.default_model = default_model

        # Configure client with retries and timeouts
        config = Config(
            region_name=region,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            connect_timeout=5,
            read_timeout`
        )

        self._runtime = boto3.client('bedrock-runtime', config=config)

    def complete(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        system: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simple completion with sensible defaults.
        """
        model = model_id or self.default_model
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }

        if system:
            body["system"] = system

        response = self._runtime.invoke_model(
            modelId=model,
            body=json.dumps(body)
        )

        result = json.loads(response['body'].read())
        return {
            'text': result['content'][0]['text'],
            'usage': result.get('usage', {}),
            'model': model
        }

    def chat(
        self,
        messages: List[Dict[str, str]],
        model_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Multi-turn conversation.
        """
        model = model_id or self.default_model

        response = self._runtime.invoke_model(
            modelId=model,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": kwargs.get('max_tokens', 1024),
                "messages": messages,
                **{k: v for k, v in kwargs.items() if k != 'max_tokens'}
            })
        )

        result = json.loads(response['body'].read())
        return {
            'text': result['content'][0]['text'],
            'usage': result.get('usage', {}),
            'stop_reason': result.get('stop_reason')
        }

    def stream(self, prompt: str, **kwargs):
        """
        Streaming completion generator.
        """
        model = kwargs.get('model_id', self.default_model)

        response = self._runtime.invoke_model_with_response_stream(
            modelId=model,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": kwargs.get('max_tokens', 1024),
                "messages": [{"role": "user", "content": prompt}]
            })
        )

        for event in response['body']:
            chunk = json.loads(event['chunk']['bytes'])
            if chunk['type'] = 'content_block_delta':
                yield chunk['delta'].get('text', '')

# Usage examples
client = BedrockClient()

# Simple completion
result = client.complete("What is AWS Lambda?")
print(result['text'])

# Conversation
conversation = [
    {"role": "user", "content": "Hello, I'm learning about AWS."},
    {"role": "assistant", "content": "Great! I'd be happy to help you learn about AWS. What would you like to know?"},
    {"role": "user", "content": "Tell me about S3."}
]
response = client.chat(conversation)
print(response['text'])

# Streaming
for chunk in client.stream("Write a haiku about clouds"):
    print(chunk, end="", flush=True)