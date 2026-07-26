import boto3
import json
import hashlib
import redis
from typing import Optional, Dict, Tuple
import numpy as np

class GenAICache:
    """Multi-layer caching for GenAI applications"""

    def __init__(
        self,
        redis_host: str,
        redis_port: int = 6379,
        embedding_model: str = 'amazon.titan-embed-text-v1',
        similarity_threshold: float = 0.92,
        ttl_seconds: int = 3600
    ):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port)
        self.bedrock = boto3.client('bedrock-runtime')
        self.embedding_model = embedding_model
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds

    def _generate_exact_key(
        self,
        prompt: str,
        model_id: str,
        params: Dict
    ) -> str:
        """Generate key for exact-match caching"""
        key_string = f"{model_id}:{prompt}:{json.dumps(params, sort_keys=True)}"
        return f"exact:{hashlib.sha256(key_string.encode()).hexdigest()}"

    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for semantic caching"""
        response = self.bedrock.invoke_model(
            modelId=self.embedding_model,
            body=json.dumps({'inputText': text})
        )
        result = json.loads(response['body'].read())
        return np.array(result['embedding'])

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def get_exact_match(
        self,
        prompt: str,
        model_id: str,
        params: Dict
    ) -> Optional[str]:
        """Check exact-match cache"""
        key = self._generate_exact_key(prompt, model_id, params)
        cached = self.redis_client.get(key)
        if cached:
            return cached.decode('utf-8')
        return None

    def set_exact_match(
        self,
        prompt: str,
        model_id: str,
        params: Dict,
        response: str
    ):
        """Store in exact-match cache"""
        key = self._generate_exact_key(prompt, model_id, params)
        self.redis_client.setex(key, self.ttl_seconds, response)

    def get_semantic_match(
        self,
        prompt: str,
        model_id: str
    ) -> Optional[Tuple[str, float]]:
        """
        Check semantic cache using embedding similarity.
        Returns (cached_response, similarity_score) or None.
        """
        prompt_embedding = self._get_embedding(prompt)

        # Get all semantic cache entries for this model
        pattern = f"semantic:{model_id}:*"
        keys = self.redis_client.keys(pattern)

        best_match = None
        best_similarity = 0.0

        for key in keys:
            cached_data = self.redis_client.hgetall(key)
            if not cached_data:
                continue

            cached_embedding = np.frombuffer(
                cached_data[b'embedding'],
                dtype=np.float32
            )
            similarity = self._cosine_similarity(prompt_embedding, cached_embedding)

            if similarity > best_similarity and similarity >= self.similarity_threshold:
                best_similarity = similarity
                best_match = cached_data[b'response'].decode('utf-8')

        if best_match:
            return (best_match, best_similarity)
        return None

    def set_semantic_cache(
        self,
        prompt: str,
        model_id: str,
        response: str
    ):
        """Store in semantic cache"""
        embedding = self._get_embedding(prompt)
        key = f"semantic:{model_id}:{hashlib.md5(prompt.encode()).hexdigest()}"

        self.redis_client.hset(key, mapping={
            'prompt': prompt,
            'response': response,
            'embedding': embedding.astype(np.float32).tobytes()
        })
        self.redis_client.expire(key, self.ttl_seconds)

    def get_cached_response(
        self,
        prompt: str,
        model_id: str,
        params: Dict,
        use_semantic: bool = True
    ) -> Optional[Dict]:
        """
        Try to get cached response, checking exact then semantic.

        Returns:
            Dict with 'response', 'cache_hit_type', 'similarity' (if semantic)
        """
        # Try exact match first
        exact_result = self.get_exact_match(prompt, model_id, params)
        if exact_result:
            return {
                'response': exact_result,
                'cache_hit_type': 'exact',
                'similarity': 1.0
            }

        # Try semantic match if enabled
        if use_semantic:
            semantic_result = self.get_semantic_match(prompt, model_id)
            if semantic_result:
                response, similarity = semantic_result
                return {
                    'response': response,
                    'cache_hit_type': 'semantic',
                    'similarity': similarity
                }

        return None


class CachedBedrockClient:
    """Bedrock client with integrated caching"""

    def __init__(self, cache: GenAICache):
        self.cache = cache
        self.bedrock = boto3.client('bedrock-runtime')

    def invoke(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.0,
        use_cache: bool = True,
        use_semantic_cache: bool = True
    ) -> Dict:
        """Invoke model with caching"""
        params = {'max_tokens': max_tokens, 'temperature': temperature}

        # Check cache
        if use_cache:
            cached = self.cache.get_cached_response(
                prompt, model_id, params, use_semantic_cache
            )
            if cached:
                return {
                    'response': cached['response'],
                    'cached': True,
                    'cache_type': cached['cache_hit_type'],
                    'similarity': cached.get('similarity', 1.0)
                }

        # Invoke model
        response = self.bedrock.converse(
            modelId=model_id,
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': max_tokens, 'temperature': temperature}
        )

        response_text = response['output']['message']['content'][0]['text']

        # Store in cache
        if use_cache:
            # Always store exact match
            self.cache.set_exact_match(prompt, model_id, params, response_text)
            # Store semantic cache for temperature=0 (deterministic)
            if temperature = 0 and use_semantic_cache:
                self.cache.set_semantic_cache(prompt, model_id, response_text)

        return {
            'response': response_text,
            'cached': False,
            'usage': response.get('usage', {})
        }


# Example usage
cache = GenAICache(
    redis_host='your-elasticache-endpoint.cache.amazonaws.com',
    similarity_threshold=0.92,
    ttl_seconds600
)

client = CachedBedrockClient(cache)

# First call - cache miss
result1 = client.invoke(
    model_id='anthropic.claude-3-haiku-20240307-v1:0',
    prompt='What is the capital of France?',
    temperature=0
)
print(f"Cached: {result1['cached']}, Response: {result1['response']}")

# Second call with same prompt - exact cache hit
result2 = client.invoke(
    model_id='anthropic.claude-3-haiku-20240307-v1:0',
    prompt='What is the capital of France?',
    temperature=0
)
print(f"Cached: {result2['cached']}, Type: {result2.get('cache_type')}")

# Similar prompt - semantic cache hit
result3 = client.invoke(
    model_id='anthropic.claude-3-haiku-20240307-v1:0',
    prompt='Tell me the capital city of France',
    temperature=0
)
print(f"Cached: {result3['cached']}, Similarity: {result3.get('similarity', 'N/A')}")