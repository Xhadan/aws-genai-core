# Two-stage retrieval
candidates = vector_search(query, k )  # Fast, coarse
reranked = rerank_model(query, candidates)  # Slow, precise
final_results = reranked[:5]  # Top relevant