# Instead of exact match
assert response = "Paris is the capital of France"

# Use semantic validation
similarity = cosine_similarity(embed(response), embed(expected))
assert similarity > 0.85