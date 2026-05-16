def adaptive_retrieve(query, knowledge_base_id, min_k=3, max_k, score_threshold=0.7):
    """
    Dynamically adjust k based on result quality.
    Start with larger k, filter by score threshold.
    """
    response = bedrock_agent_runtime.retrieve(
        knowledgeBaseId=knowledge_base_id,
        retrievalQuery={'text': query},
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': max_k,
                'overrideSearchType': 'HYBRID'
            }
        }
    )

    # Filter by score threshold
    high_quality_results = [
        r for r in response['retrievalResults']
        if r.get('score', 0) >= score_threshold
    ]

    # Ensure minimum results
    if len(high_quality_results) < min_k:
        return response['retrievalResults'][:min_k]

    return high_quality_results