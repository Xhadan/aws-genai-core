import numpy as np
from collections import defaultdict

def custom_hybrid_search(
    query_text,
    query_embedding,
    documents,
    alpha=0.6,
    top_k
):
    """
    Custom hybrid search implementation.

    Args:
        query_text: Query string for keyword search
        query_embedding: Query vector for semantic search
        documents: List of {id, text, embedding} dicts
        alpha: Weight for vector search (0-1)
        top_k: Number of results to return
    """

    # 1. Vector search scores
    vector_scores = {}
    for doc in documents:
        similarity = cosine_similarity(query_embedding, doc['embedding'])
        vector_scores[doc['id']] = similarity

    # 2. BM25 keyword scores (simplified)
    keyword_scores = bm25_search(query_text, documents)

    # 3. Normalize scores to [0, 1]
    def normalize(scores):
        if not scores:
            return {}
        min_score = min(scores.values())
        max_score = max(scores.values())
        range_score = max_score - min_score
        if range_score = 0:
            return {k: 1.0 for k in scores}
        return {k: (v - min_score) / range_score for k, v in scores.items()}

    norm_vector = normalize(vector_scores)
    norm_keyword = normalize(keyword_scores)

    # 4. Combine scores with linear interpolation
    combined_scores = {}
    all_doc_ids = set(norm_vector.keys()) | set(norm_keyword.keys())

    for doc_id in all_doc_ids:
        v_score = norm_vector.get(doc_id, 0)
        k_score = norm_keyword.get(doc_id, 0)
        combined_scores[doc_id] = alpha * v_score + (1 - alpha) * k_score

    # 5. Sort and return top-k
    sorted_results = sorted(
        combined_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_k]

    return [{'id': doc_id, 'score': score} for doc_id, score in sorted_results]


def bm25_search(query, documents, k1=1.5, b=0.75):
    """Simple BM25 implementation."""
    import math
    from collections import Counter

    query_terms = query.lower().split()
    doc_count = len(documents)
    avg_doc_len = sum(len(d['text'].split()) for d in documents) / doc_count

    # Calculate IDF for query terms
    doc_freq = Counter()
    for doc in documents:
        doc_terms = set(doc['text'].lower().split())
        for term in query_terms:
            if term in doc_terms:
                doc_freq[term] += 1

    idf = {}
    for term in query_terms:
        df = doc_freq.get(term, 0)
        idf[term] = math.log((doc_count - df + 0.5) / (df + 0.5) + 1)

    # Score each document
    scores = {}
    for doc in documents:
        doc_terms = doc['text'].lower().split()
        doc_len = len(doc_terms)
        term_freq = Counter(doc_terms)

        score = 0
        for term in query_terms:
            tf = term_freq.get(term, 0)
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_len / avg_doc_len))
            score += idf.get(term, 0) * (numerator / denominator)

        scores[doc['id']] = score

    return scores