import aioboto3
import asyncio
import json
from typing import AsyncGenerator

class AsyncBedrockService:
    """Async Bedrock client using aioboto3."""

    def __init__(self, region_name: str = "us-east-1"):
        self.region = region_name
        self.session = aioboto3.Session()

    async def invoke_model(
        self,
        prompt: str,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    ) -> str:
        """Async model invocation."""
        async with self.session.client('bedrock-runtime', region_name=self.region) as client:
            response = await client.invoke_model(
                modelId=model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )

            result = json.loads(await response['body'].read())
            return result['content'][0]['text']

    async def invoke_many(
        self,
        prompts: list,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        max_concurrent: int = 5
    ) -> list:
        """Invoke multiple prompts concurrently with rate limiting."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def invoke_with_limit(prompt: str) -> dict:
            async with semaphore:
                try:
                    result = await self.invoke_model(prompt, model_id)
                    return {'prompt': prompt, 'result': result, 'error': None}
                except Exception as e:
                    return {'prompt': prompt, 'result': None, 'error': str(e)}

        tasks = [invoke_with_limit(p) for p in prompts]
        return await asyncio.gather(*tasks)

# Usage
async def main():
    service = AsyncBedrockService()

    # Single invocation
    result = await service.invoke_model("What is AWS Lambda?")
    print(result)

    # Multiple concurrent invocations
    prompts = [
        "Explain S3",
        "Explain EC2",
        "Explain DynamoDB",
        "Explain Lambda",
        "Explain Bedrock"
    ]

    results = await service.invoke_many(prompts, max_concurrent=3)
    for r in results:
        if r['error']:
            print(f"Error for '{r['prompt'][:20]}...': {r['error']}")
        else:
            print(f"Success for '{r['prompt'][:20]}...': {len(r['result'])} chars")

# Run
asyncio.run(main())