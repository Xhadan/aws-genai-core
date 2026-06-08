import boto3

agentcore = boto3.client('bedrock-agentcore')

# Store a memory record explicitly
agentcore.create_memory_record(
    memoryStoreId='customer-service-memory',
    userId='user-12345',
    memoryRecord={
        'strategyType': 'SEMANTIC',
        'content': {
            'fact': 'Customer prefers express shipping',
            'confidence': 0.95,
            'source': 'explicit_statement'
        },
        'metadata': {
            'sessionId': 'session-abc123',
            'timestamp': '2025-01-15T10:30:00Z'
        }
    }
)

# Retrieve memories for a user
memories = agentcore.retrieve_memory_records(
    memoryStoreId='customer-service-memory',
    userId='user-12345',

    # Semantic search query
    query='shipping preferences',

    # Filter by strategy
    strategyTypes=['SEMANTIC', 'USER_PREFERENCES'],

    # Limit results
    maxResults,

    # Time range filter
    timeRange={
        'startTime': '2024-01-01T00:00:00Z',
        'endTime': '2025-01-15T23:59:59Z'
    }
)

print(f"Found {len(memories['records'])} relevant memories")
for record in memories['records']:
    print(f"Type: {record['strategyType']}")
    print(f"Content: {record['content']}")
    print(f"Relevance: {record['relevanceScore']}")
    print("---")

# Delete specific memories (for compliance/GDPR)
agentcore.delete_memory_records(
    memoryStoreId='customer-service-memory',
    userId='user-12345',
    recordIds=['record-001', 'record-002']
)

# Delete all memories for a user (right to be forgotten)
agentcore.delete_user_memories(
    memoryStoreId='customer-service-memory',
    userId='user-12345'
)