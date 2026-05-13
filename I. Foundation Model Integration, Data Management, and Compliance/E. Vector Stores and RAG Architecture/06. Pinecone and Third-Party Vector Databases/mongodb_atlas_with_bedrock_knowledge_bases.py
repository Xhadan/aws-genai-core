import boto3

bedrock_agent = boto3.client('bedrock-agent')

# Create Knowledge Base with MongoDB Atlas
kb_response = bedrock_agent.create_knowledge_base(
    name='mongodb-rag-kb',
    roleArn='arn:aws:iam::123456789012:role/BedrockKBRole',
    knowledgeBaseConfiguration={
        'type': 'VECTOR',
        'vectorKnowledgeBaseConfiguration': {
            'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0'
        }
    },
    storageConfiguration={
        'type': 'MONGO_DB_ATLAS',
        'mongoDbAtlasConfiguration': {
            'endpoint': 'my-cluster.abc123.mongodb.net',
            'credentialsSecretArn': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:mongodb-creds',
            'databaseName': 'rag_database',
            'collectionName': 'document_chunks',
            'vectorIndexName': 'vector_index',
            'fieldMapping': {
                'vectorField': 'embedding',
                'textField': 'content',
                'metadataField': 'metadata'
            }
        }
    }
)