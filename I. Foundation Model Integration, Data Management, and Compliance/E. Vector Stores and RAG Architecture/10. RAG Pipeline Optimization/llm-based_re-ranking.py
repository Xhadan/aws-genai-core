def llm_rerank(query, documents, top_k=5):
    """
    Use LLM to re-rank documents based on relevance.
    More expensive but handles complex relevance judgments.
    """

    docs_text = "\n\n".join([
        f"[Document {i+1}]\n{doc['text'][:500]}"
        for i, doc in enumerate(documents)
    ])

    prompt = f"""Given the query and documents below, rank the documents by relevance.
Return only the document numbers in order of relevance, most relevant first.

Query: {query}

Documents:
{docs_text}

Return format: comma-separated numbers (e.g., "3,1,5,2,4")"""

    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 64,
            'temperature': 0
        })
    )

    ranking_str = json.loads(response['body'].read())['content'][0]['text']
    rankings = [int(x.strip()) - 1 for x in ranking_str.split(',')]

    return [documents[i] for i in rankings[:top_k]]