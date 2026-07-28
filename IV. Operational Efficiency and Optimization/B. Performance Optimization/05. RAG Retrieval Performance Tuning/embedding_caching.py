# Redis-based embedding cache
cache_key = hashlib.sha256(query.encode()).hexdigest()
cached_embedding = redis.get(f"emb:{cache_key}")

if cached_embedding:
    embedding = np.frombuffer(cached_embedding)
else:
    embedding = generate_embedding(query)
    redis.setex(f"emb:{cache_key}", 3600, embedding.tobytes())