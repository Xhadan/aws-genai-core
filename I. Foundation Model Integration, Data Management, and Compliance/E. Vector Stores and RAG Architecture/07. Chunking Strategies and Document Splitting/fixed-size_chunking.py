import boto3

bedrock_agent = boto3.client('bedrock-agent')

# Fixed-size chunking configuration
fixed_chunking_config = {
    'chunkingStrategy': 'FIXED_SIZE',
    'fixedSizeChunkingConfiguration': {
        'maxTokens': 300,          # Tokens per chunk
        'overlapPercentage': 20    # 20% overlap
    }
}

# Create data source with fixed chunking
response = bedrock_agent.create_data_source(
    knowledgeBaseId='KB12345678',
    name='fixed-chunking-source',
    dataSourceConfiguration={
        's3Configuration': {
            'bucketArn': 'arn:aws:s3:::my-documents'
        }
    },
    vectorIngestionConfiguration={
        'chunkingConfiguration': fixed_chunking_config
    }
)