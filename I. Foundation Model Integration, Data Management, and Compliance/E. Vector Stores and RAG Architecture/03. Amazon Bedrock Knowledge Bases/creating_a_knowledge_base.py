import boto3

bedrock_agent = boto3.client('bedrock-agent')

# Step 1: Create Knowledge Base
kb_response = bedrock_agent.create_knowledge_base(
    name='enterprise-docs-kb',
    description='Enterprise documentation knowledge base',
    roleArn='arn:aws:iam::123456789012:role/BedrockKBRole',
    knowledgeBaseConfiguration={
        'type': 'VECTOR',
        'vectorKnowledgeBaseConfiguration': {
            'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0',
            'embeddingModelConfiguration': {
                'bedrockEmbeddingModelConfiguration': {
                    'dimensions': 1024
                }
            }
        }
    },
    storageConfiguration={
        'type': 'OPENSEARCH_SERVERLESS',
        'opensearchServerlessConfiguration': {
            'collectionArn': 'arn:aws:aoss:us-east-1:123456789012:collection/abc123',
            'vectorIndexName': 'bedrock-knowledge-base-index',
            'fieldMapping': {
                'vectorField': 'bedrock-knowledge-base-vector',
                'textField': 'AMAZON_BEDROCK_TEXT',
                'metadataField': 'AMAZON_BEDROCK_METADATA'
            }
        }
    }
)

kb_id = kb_response['knowledgeBase']['knowledgeBaseId']