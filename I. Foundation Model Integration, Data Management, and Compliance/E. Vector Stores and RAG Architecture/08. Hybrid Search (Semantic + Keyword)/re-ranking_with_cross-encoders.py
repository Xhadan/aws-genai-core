import boto3
import json

bedrock = boto3.client('bedrock-runtime')

def rerank_with_cohere(query, documents, top_n=5):
    """
    Re-rank documents using Cohere Rerank model on Bedrock.
    """
    # Format documents for Cohere
    doc_texts = [doc['text'] for doc in documents]

    response = bedrock.invoke_model(
        modelId='cohere.rerank-v3-5:0',
        body=json.dumps({
            'query': query,
            'documents': doc_texts,
            'top_n': top_n
        })
    )

    result = json.loads(response['body'].read())

    # Return reranked documents
    reranked = []
    for item in result['results']:
        reranked.append({
            'document': documents[item['index']],
            'relevance_score': item['relevance_score']
        })

    return reranked


# Two-stage retrieval pipeline
def hybrid_retrieve_and_rerank(query, knowledge_base_id, initial_kP, final_k=5):
    """Hybrid retrieval with re-ranking."""

    # Stage 1: Hybrid retrieval
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

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

    documents = [
        {'text': r['content']['text'], 'location': r['location']}
        for r in initial_results['retrievalResults']
    ]

    # Stage 2: Re-rank
    reranked = rerank_with_cohere(query, documents, top_n=final_k)

    return reranked