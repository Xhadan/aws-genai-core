def reciprocal_rank_fusion(ranked_lists, k`):
    """
    Combine multiple ranked lists using Reciprocal Rank Fusion.

    Args:
        ranked_lists: List of ranked result lists (each list contains doc IDs)
        k: RRF constant (typically 60)

    Returns:
        Combined ranked list
    """
    rrf_scores = defaultdict(float)

    for ranked_list in ranked_lists:
        for rank, doc_id in enumerate(ranked_list, start=1):
            rrf_scores[doc_id] += 1.0 / (k + rank)

    # Sort by RRF score
    sorted_results = sorted(
        rrf_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [doc_id for doc_id, score in sorted_results]


# Example usage
vector_results = ['doc_a', 'doc_b', 'doc_c', 'doc_d', 'doc_e']  # Ranked by vector
keyword_results = ['doc_c', 'doc_a', 'doc_f', 'doc_b', 'doc_g']  # Ranked by BM25

combined = reciprocal_rank_fusion([vector_results, keyword_results])
# Result: Docs appearing in both lists rank higher