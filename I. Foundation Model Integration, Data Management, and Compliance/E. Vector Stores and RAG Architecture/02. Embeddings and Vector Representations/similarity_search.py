import numpy as np

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between vectors."""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# Example: Find most similar documents
query_embedding = get_embedding("How do I deploy a Lambda function?")

# Compare with document embeddings
similarities = []
for doc_id, doc_embedding in document_embeddings.items():
    sim = cosine_similarity(query_embedding, doc_embedding)
    similarities.append((doc_id, sim))

# Sort by similarity (highest first)
similarities.sort(key=lambda x: x[1], reverse=True)
top_k = similarities[:5]  # Top 5 most similar