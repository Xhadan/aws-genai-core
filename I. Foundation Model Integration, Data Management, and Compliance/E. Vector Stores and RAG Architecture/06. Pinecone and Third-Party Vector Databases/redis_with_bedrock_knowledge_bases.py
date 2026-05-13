import boto3

bedrock_agent = boto3.client('bedrock-agent')

# Create Knowledge Base with Redis Enterprise
kb_response = bedrock_agent.create_knowledge_base(
    name='redis-rag-kb',
    roleArn='arn:aws:iam::123456789012:role/BedrockKBRole',
    knowledgeBaseConfiguration={
        'type': 'VECTOR',
        'vectorKnowledgeBaseConfiguration': {
            'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0'
        }
    },
    storageConfiguration={
        'type': 'REDIS_ENTERPRISE_CLOUD',
        'redisEnterpriseCloudConfiguration': {
            'endpoint': 'redis-12345.c1.us-east-1-1.ec2.cloud.redislabs.com:12345',
            'credentialsSecretArn': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:redis-creds',
            'vectorIndexName': 'rag_index',
            'fieldMapping': {
                'vectorField': 'embedding',
                'textField': 'content',
                'metadataField': 'metadata'
            }
        }
    }
)