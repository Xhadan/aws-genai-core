# Semantic chunking configuration
semantic_chunking_config = {
    'chunkingStrategy': 'SEMANTIC',
    'semanticChunkingConfiguration': {
        'maxTokens': 512,                     # Max tokens per chunk
        'bufferSize': 0,                      # Sentences to include around break
        'breakpointPercentileThreshold': 95   # 95 = more aggressive splitting
    }
}

# Create data source with semantic chunking
response = bedrock_agent.create_data_source(
    knowledgeBaseId='KB12345678',
    name='semantic-chunking-source',
    dataSourceConfiguration={
        's3Configuration': {
            'bucketArn': 'arn:aws:s3:::my-documents'
        }
    },
    vectorIngestionConfiguration={
        'chunkingConfiguration': semantic_chunking_config
    }
)

# Breakpoint threshold explanation:
# - Higher (95-99): Fewer, larger chunks (less aggressive splitting)
# - Lower (80-90): More, smaller chunks (more aggressive splitting)