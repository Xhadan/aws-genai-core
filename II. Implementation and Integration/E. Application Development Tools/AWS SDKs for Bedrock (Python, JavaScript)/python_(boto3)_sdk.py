import boto3
import json
from botocore.config import Config
from typing import Generator, Optional

class BedrockService:
    """Production-ready boto3 Bedrock client wrapper."""

    def __init__(
        self,
        region_name: str = "us-east-1",
        profile_name: Optional[str] = None
    ):
        # Configure client with retries and timeouts
        config = Config(
            region_name=region_name,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'  # Smart retry with backoff
            },
            connect_timeout=5,
            read_timeout0  # Long timeout for FM responses
        )

        session_kwargs = {}
        if profile_name:
            session_kwargs['profile_name'] = profile_name

        session = boto3.Session(**session_kwargs)

        # Data plane client for invocations
        self.runtime = session.client('bedrock-runtime', config=config)

        # Control plane client for management
        self.bedrock = session.client('bedrock', config=config)

        # Agent runtime for agent invocations
        self.agent_runtime = session.client('bedrock-agent-runtime', config=config)

    def invoke_model(
        self,
        prompt: str,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        system: Optional[str] = None
    ) -> dict:
        """Invoke a foundation model."""

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        if system:
            body["system"] = system

        response = self.runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )

        result = json.loads(response['body'].read())

        return {
            'text': result['content'][0]['text'],
            'usage': result.get('usage', {}),
            'stop_reason': result.get('stop_reason')
        }

    def invoke_model_stream(
        self,
        prompt: str,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        max_tokens: int = 1024
    ) -> Generator[str, None, None]:
        """Stream model response."""

        response = self.runtime.invoke_model_with_response_stream(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            })
        )

        for event in response['body']:
            chunk = json.loads(event['chunk']['bytes'])

            if chunk['type'] = 'content_block_delta':
                yield chunk['delta'].get('text', '')

    def invoke_with_guardrail(
        self,
        prompt: str,
        guardrail_id: str,
        guardrail_version: str = "DRAFT",
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    ) -> dict:
        """Invoke model with guardrail."""

        response = self.runtime.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}]
            }),
            guardrailIdentifier=guardrail_id,
            guardrailVersion=guardrail_version
        )

        result = json.loads(response['body'].read())

        return {
            'text': result['content'][0]['text'],
            'guardrail_action': result.get('amazon-bedrock-guardrailAction')
        }

    def list_models(self) -> list:
        """List available foundation models."""
        response = self.bedrock.list_foundation_models()
        return [
            {
                'id': model['modelId'],
                'name': model['modelName'],
                'provider': model['providerName'],
                'modalities': model.get('inputModalities', [])
            }
            for model in response['modelSummaries']
        ]

# Usage
service = BedrockService(region_name="us-east-1")

# Simple invocation
result = service.invoke_model("Explain quantum computing in simple terms.")
print(result['text'])

# Streaming
for chunk in service.invoke_model_stream("Write a short poem about clouds."):
    print(chunk, end="", flush=True)