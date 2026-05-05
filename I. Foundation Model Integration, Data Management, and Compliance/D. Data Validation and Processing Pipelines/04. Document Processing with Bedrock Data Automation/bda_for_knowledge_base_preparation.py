import boto3

# BDA automatically prepares documents during Knowledge Base ingestion
bedrock_agent = boto3.client('bedrock-agent')

# Create data source with BDA enabled
response = bedrock_agent.create_data_source(
    knowledgeBaseId='my-knowledge-base',
    name='enterprise-docs',
    dataSourceConfiguration={
        's3Configuration': {
            'bucketArn': 'arn:aws:s3:::my-documents-bucket',
            'inclusionPrefixes': ['documents/']
        }
    },
    dataDeletionPolicy='DELETE',
    vectorIngestionConfiguration={
        'chunkingConfiguration': {
            'chunkingStrategy': 'SEMANTIC',
            'semanticChunkingConfiguration': {
                'maxTokens': 512,
                'bufferSize': 0,
                'breakpointPercentileThreshold': 95
            }
        },
        'parsingConfiguration': {
            'parsingStrategy': 'BEDROCK_DATA_AUTOMATION',  # Use BDA
            'bedrockDataAutomationConfiguration': {
                'parsingModality': 'MULTIMODAL'  # Text + images
            }
        }
    }
)