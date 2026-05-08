# Fixed-size chunking
fixed_chunking = {
    'chunkingStrategy': 'FIXED_SIZE',
    'fixedSizeChunkingConfiguration': {
        'maxTokens': 300,
        'overlapPercentage': 20  # 20% overlap between chunks
    }
}

# Semantic chunking
semantic_chunking = {
    'chunkingStrategy': 'SEMANTIC',
    'semanticChunkingConfiguration': {
        'maxTokens': 512,
        'bufferSize': 0,
        'breakpointPercentileThreshold': 95
    }
}

# Hierarchical chunking
hierarchical_chunking = {
    'chunkingStrategy': 'HIERARCHICAL',
    'hierarchicalChunkingConfiguration': {
        'levelConfigurations': [
            {'maxTokens': 1500},  # Parent chunks
            {'maxTokens': 300}    # Child chunks
        ],
        'overlapTokens': 60
    }
}