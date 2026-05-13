import boto3

bedrock_agent = boto3.client('bedrock-agent')

# Create Knowledge Base with Aurora PostgreSQL
kb_response = bedrock_agent.create_knowledge_base(
    name='aurora-pgvector-kb',
    roleArn='arn:aws:iam::123456789012:role/BedrockKBRole',
    knowledgeBaseConfiguration={
        'type': 'VECTOR',
        'vectorKnowledgeBaseConfiguration': {
            'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0'
        }
    },
    storageConfiguration={
        'type': 'RDS',
        'rdsConfiguration': {
            'resourceArn': 'arn:aws:rds:us-east-1:123456789012:cluster:my-aurora-cluster',
            'credentialsSecretArn': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:rds-creds',
            'databaseName': 'ragdb',
            'tableName': 'bedrock_knowledge_base',
            'fieldMapping': {
                'primaryKeyField': 'id',
                'vectorField': 'embedding',
                'textField': 'content',
                'metadataField': 'metadata'
            }
        }
    }
)