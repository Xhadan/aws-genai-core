import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

def rag_query(knowledge_base_id, query, model_id="anthropic.claude-3-sonnet-20240229-v1:0"):
    """Execute RAG query against Bedrock Knowledge Base."""

    # Retrieve relevant documents
    retrieve_response = bedrock_agent_runtime.retrieve(
        knowledgeBaseId=knowledge_base_id,
        retrievalQuery={'text': query},
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': 5
            }
        }
    )

    # Extract retrieved context
    contexts = []
    sources = []
    for result in retrieve_response['retrievalResults']:
        contexts.append(result['content']['text'])
        sources.append(result['location'])

    # Augment prompt with retrieved context
    augmented_prompt = f"""Based on the following information, answer the question.

Context:
{chr(10).join(contexts)}

Question: {query}

Provide a detailed answer based on the context above. If the context doesn't contain relevant information, say so."""

    # Generate response
    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [{"role": "user", "content": augmented_prompt}],
            "max_tokens": 1024
        })
    )

    result = json.loads(response['body'].read())
    return {
        'answer': result['content'][0]['text'],
        'sources': sources
    }