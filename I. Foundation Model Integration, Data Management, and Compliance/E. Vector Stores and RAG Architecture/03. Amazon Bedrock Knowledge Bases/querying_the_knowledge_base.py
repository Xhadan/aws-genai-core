bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

# Option 1: Retrieve only (for custom generation)
retrieve_response = bedrock_agent_runtime.retrieve(
    knowledgeBaseId=kb_id,
    retrievalQuery={'text': "What is our refund policy?"},
    retrievalConfiguration={
        'vectorSearchConfiguration': {
            'numberOfResults': 5,
            'overrideSearchType': 'HYBRID'  # Vector + keyword
        }
    }
)

# Option 2: Retrieve and Generate (full RAG)
rag_response = bedrock_agent_runtime.retrieve_and_generate(
    input={'text': "Summarize our vacation policy"},
    retrieveAndGenerateConfiguration={
        'type': 'KNOWLEDGE_BASE',
        'knowledgeBaseConfiguration': {
            'knowledgeBaseId': kb_id,
            'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0'
        }
    }
)

print(rag_response['output']['text'])