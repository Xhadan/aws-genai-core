def hyde_retrieve(query, knowledge_base_id):
    """
    Generate hypothetical answer, use it for retrieval.
    Often improves retrieval for complex queries.
    """

    # Generate hypothetical document/answer
    hyde_prompt = f"""Write a short, factual paragraph that would answer this question:

Question: {query}

Write as if you're excerpting from an official document. Be specific and detailed."""

    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'messages': [{'role': 'user', 'content': hyde_prompt}],
            'max_tokens': 256,
            'temperature': 0.5
        })
    )

    hypothetical_doc = json.loads(response['body'].read())['content'][0]['text']

    # Use hypothetical document for retrieval
    # This often matches better than the original query
    response = bedrock_agent_runtime.retrieve(
        knowledgeBaseId=knowledge_base_id,
        retrievalQuery={'text': hypothetical_doc},
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': 10
            }
        }
    )

    return response['retrievalResults']