# Hierarchical chunking configuration
hierarchical_chunking_config = {
    'chunkingStrategy': 'HIERARCHICAL',
    'hierarchicalChunkingConfiguration': {
        'levelConfigurations': [
            {'maxTokens': 1500},  # Parent chunks (larger context)
            {'maxTokens': 300}    # Child chunks (specific details)
        ],
        'overlapTokens': 60       # Overlap between chunks
    }
}

# Create data source with hierarchical chunking
response = bedrock_agent.create_data_source(
    knowledgeBaseId='KB12345678',
    name='hierarchical-chunking-source',
    dataSourceConfiguration={
        's3Configuration': {
            'bucketArn': 'arn:aws:s3:::my-documents'
        }
    },
    vectorIngestionConfiguration={
        'chunkingConfiguration': hierarchical_chunking_config
    }
)

# Use case: Technical documentation
# Parent chunk: Entire section about "Authentication"
# Child chunks: Specific subsections (OAuth, JWT, API Keys)