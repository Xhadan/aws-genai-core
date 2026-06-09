import boto3

agentcore = boto3.client('bedrock-agentcore')

# Create a shared memory store
response = agentcore.create_memory_store(
    memoryStoreName='shared-research-memory',
    description='Shared memory for research agent team',

    # Sharing configuration
    sharingConfig={
        'enabled': True,
        'defaultAccessMode': 'READ_ONLY'
    },

    memoryStrategies=[
        {
            'strategyType': 'SEMANTIC',
            'enabled': True
        },
        {
            'strategyType': 'EPISODIC',
            'enabled': True,
            'config': {
                'reflectionEnabled': True
            }
        }
    ]
)

memory_store_id = response['memoryStoreId']

# Grant access to specific agents
agentcore.share_memory_store(
    memoryStoreId=memory_store_id,
    shares=[
        {
            'agentId': 'research-agent',
            'accessMode': 'READ_WRITE'  # Can add memories
        },
        {
            'agentId': 'analysis-agent',
            'accessMode': 'READ_WRITE'
        },
        {
            'agentId': 'reporting-agent',
            'accessMode': 'READ_ONLY'  # Can only read
        }
    ]
)

# Agents automatically access shared memory in their sessions
# Research agent writes findings:
agentcore.create_memory_record(
    memoryStoreId=memory_store_id,
    userId='project-alpha',  # Can use project ID instead of user
    memoryRecord={
        'strategyType': 'SEMANTIC',
        'content': {
            'finding': 'Market analysis shows 15% growth in Q4',
            'source': 'research-agent',
            'confidence': 0.9
        }
    }
)

# Analysis agent can immediately access this memory
# Reporting agent can read it when generating reports