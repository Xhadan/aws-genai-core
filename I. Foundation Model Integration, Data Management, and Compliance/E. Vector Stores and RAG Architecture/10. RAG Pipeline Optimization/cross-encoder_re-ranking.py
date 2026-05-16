def retrieve_and_rerank(query, knowledge_base_id, initial_kP, final_k=5):
    """
    Two-stage retrieval: fast initial retrieval + precise re-ranking.
    """

    # Stage 1: Fast retrieval with larger k
    initial_results = bedrock_agent_runtime.retrieve(
        knowledgeBaseId=knowledge_base_id,
        retrievalQuery={'text': query},
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': initial_k,
                'overrideSearchType': 'HYBRID'
            }
        }
    )

    documents = [r['content']['text'] for r in initial_results['retrievalResults']]

    # Stage 2: Re-rank with Cohere
    rerank_response = bedrock.invoke_model(
        modelId='cohere.rerank-v3-5:0',
        body=json.dumps({
            'query': query,
            'documents': documents,
            'top_n': final_k
        })
    )

    rerank_result = json.loads(rerank_response['body'].read())

    # Map back to original results with locations
    reranked_results = []
    for item in rerank_result['results']:
        original_result = initial_results['retrievalResults'][item['index']]
        reranked_results.append({
            'content': original_result['content'],
            'location': original_result['location'],
            'original_score': original_result.get('score', 0),
            'rerank_score': item['relevance_score']
        })

    return reranked_results