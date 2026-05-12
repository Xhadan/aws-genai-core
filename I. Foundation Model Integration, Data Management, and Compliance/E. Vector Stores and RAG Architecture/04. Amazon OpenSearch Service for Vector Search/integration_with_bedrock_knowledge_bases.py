import boto3

bedrock_agent = boto3.client('bedrock-agent')

# Create Knowledge Base with OpenSearch Serverless
kb_response = bedrock_agent.create_knowledge_base(
    name='rag-knowledge-base',
    roleArn='arn:aws:iam::123456789012:role/BedrockKBRole',
    knowledgeBaseConfiguration={
        'type': 'VECTOR',
        'vectorKnowledgeBaseConfiguration': {
            'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0'
        }
    },
    storageConfiguration={
        'type': 'OPENSEARCH_SERVERLESS',
        'opensearchServerlessConfiguration': {
            'collectionArn': 'arn:aws:aoss:us-east-1:123456789012:collection/abc123',
            'vectorIndexName': 'bedrock-kb-index',
            'fieldMapping': {
                'vectorField': 'embedding',
                'textField': 'text',
                'metadataField': 'metadata'
            }
        }
    }
)