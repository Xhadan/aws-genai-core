import boto3

bedrock_agent = boto3.client('bedrock-agent')

# Create Knowledge Base with Pinecone
kb_response = bedrock_agent.create_knowledge_base(
    name='pinecone-rag-kb',
    roleArn='arn:aws:iam::123456789012:role/BedrockKBRole',
    knowledgeBaseConfiguration={
        'type': 'VECTOR',
        'vectorKnowledgeBaseConfiguration': {
            'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0'
        }
    },
    storageConfiguration={
        'type': 'PINECONE',
        'pineconeConfiguration': {
            'connectionString': 'https://my-index-abc123.svc.us-east-1.pinecone.io',
            'credentialsSecretArn': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:pinecone-api-key',
            'namespace': 'bedrock-kb',  # Optional: isolate KB data
            'fieldMapping': {
                'textField': 'text',
                'metadataField': 'metadata'
            }
        }
    }
)