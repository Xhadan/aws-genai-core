class EmbeddingCache:
    """
    Cache embeddings to avoid repeated API calls.
    """

    def __init__(self, redis_client, ttl400):
        self.redis = redis_client
        self.ttl = ttl
        self.bedrock = boto3.client('bedrock-runtime')

    def get_embedding(self, text, model_id='amazon.titan-embed-text-v2:0'):
        """Get embedding from cache or generate."""
        cache_key = f"emb:{hashlib.sha256(text.encode()).hexdigest()}"

        # Check cache
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # Generate embedding
        response = self.bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps({
                'inputText': text,
                'dimensions': 1024,
                'normalize': True
            })
        )

        embedding = json.loads(response['body'].read())['embedding']

        # Cache embedding
        self.redis.setex(cache_key, self.ttl, json.dumps(embedding))

        return embedding

    def batch_get_embeddings(self, texts):
        """Batch embedding with caching."""
        results = []
        uncached = []
        uncached_indices = []

        # Check cache for all texts
        for i, text in enumerate(texts):
            cache_key = f"emb:{hashlib.sha256(text.encode()).hexdigest()}"
            cached = self.redis.get(cache_key)

            if cached:
                results.append((i, json.loads(cached)))
            else:
                uncached.append(text)
                uncached_indices.append(i)

        # Generate uncached embeddings
        for i, text in zip(uncached_indices, uncached):
            embedding = self.get_embedding(text)
            results.append((i, embedding))

        # Sort by original index
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]