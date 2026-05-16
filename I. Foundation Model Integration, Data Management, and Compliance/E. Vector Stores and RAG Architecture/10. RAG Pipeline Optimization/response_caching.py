import redis
import hashlib
import json

# Connect to ElastiCache Redis
redis_client = redis.Redis(
    host='my-cache.abc123.cache.amazonaws.com',
    portc79,
    decode_responses=True
)

def cached_rag_query(query, knowledge_base_id, cache_ttl600):
    """
    Cache RAG responses to reduce latency and cost.
    """
    # Create cache key from query + KB ID
    cache_key = hashlib.sha256(
        f"{knowledge_base_id}:{query}".encode()
    ).hexdigest()

    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Execute RAG query
    response = bedrock_agent_runtime.retrieve_and_generate(
        input={'text': query},
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': knowledge_base_id,
                'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0'
            }
        }
    )

    result = {
        'answer': response['output']['text'],
        'citations': response.get('citations', [])
    }

    # Cache response
    redis_client.setex(cache_key, cache_ttl, json.dumps(result))

    return result