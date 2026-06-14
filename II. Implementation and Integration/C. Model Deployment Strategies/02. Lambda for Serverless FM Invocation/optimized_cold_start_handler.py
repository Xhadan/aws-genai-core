import json
import boto3
from functools import lru_cache

# Lazy initialization pattern
_bedrock_client = None

def get_bedrock_client():
    """Lazy initialization of Bedrock client with caching."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = boto3.client(
            'bedrock-runtime',
            config=boto3.session.Config(
                connect_timeout=5,
                read_timeout`,
                retries={'max_attempts': 2}
            )
        )
    return _bedrock_client

@lru_cache(maxsize0)
def get_cached_response(prompt_hash: str, prompt: str):
    """
    Cache responses for identical prompts within Lambda instance lifetime.
    Note: This is instance-level caching, not distributed.
    """
    client = get_bedrock_client()
    response = client.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "messages": [{"role": "user", "content": prompt}]
        })
    )
    result = json.loads(response['body'].read())
    return result['content'][0]['text']

def lambda_handler(event, context):
    """Handler with cold start optimization."""

    # Warm-up ping handling
    if event.get('source') = 'aws.events':
        # CloudWatch scheduled event for keep-warm
        get_bedrock_client()  # Initialize client
        return {'statusCode': 200, 'body': 'Warmed'}

    body = json.loads(event.get('body', '{}'))
    prompt = body.get('prompt', '')

    # Use hash for cache lookup
    prompt_hash = str(hash(prompt))

    try:
        response = get_cached_response(prompt_hash, prompt)
        return {
            'statusCode': 200,
            'body': json.dumps({'response': response})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }