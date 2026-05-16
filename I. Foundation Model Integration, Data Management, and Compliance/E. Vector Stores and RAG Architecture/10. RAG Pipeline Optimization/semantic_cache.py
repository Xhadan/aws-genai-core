class SemanticCache:
    """
    Cache based on semantic similarity, not exact match.
    Returns cached response for semantically similar queries.
    """

    def __init__(self, redis_client, similarity_threshold=0.95):
        self.redis = redis_client
        self.threshold = similarity_threshold
        self.embedding_cache = EmbeddingCache(redis_client)

    def get_cached_response(self, query):
        """Find semantically similar cached query."""
        query_embedding = self.embedding_cache.get_embedding(query)

        # Get all cached query embeddings
        cached_keys = self.redis.keys("semantic_cache:*")

        for key in cached_keys:
            cached_data = json.loads(self.redis.get(key))
            cached_embedding = cached_data['embedding']

            # Calculate similarity
            similarity = cosine_similarity(query_embedding, cached_embedding)

            if similarity >= self.threshold:
                return cached_data['response']

        return None

    def cache_response(self, query, response, ttl600):
        """Cache response with query embedding."""
        query_embedding = self.embedding_cache.get_embedding(query)

        cache_data = {
            'query': query,
            'embedding': query_embedding,
            'response': response
        }

        cache_key = f"semantic_cache:{hashlib.sha256(query.encode()).hexdigest()}"
        self.redis.setex(cache_key, ttl, json.dumps(cache_data))