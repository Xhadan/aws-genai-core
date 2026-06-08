import boto3

agentcore = boto3.client('bedrock-agentcore')

# Create a memory store with configured strategies
response = agentcore.create_memory_store(
    memoryStoreName='customer-service-memory',
    description='Memory for customer service agents',

    # Configure memory strategies
    memoryStrategies=[
        {
            'strategyType': 'SEMANTIC',
            'enabled': True,
            'config': {
                'extractionTrigger': 'AFTER_EACH_TURN',
                'consolidationEnabled': True,
                'consolidationThreshold': 5  # Merge after 5 similar memories
            }
        },
        {
            'strategyType': 'EPISODIC',
            'enabled': True,
            'config': {
                'extractionTrigger': 'END_OF_SESSION',
                'reflectionEnabled': True,
                'minInteractionsForEpisode': 3
            }
        },
        {
            'strategyType': 'USER_PREFERENCES',
            'enabled': True,
            'config': {
                'extractionTrigger': 'AFTER_EACH_TURN',
                'inferredPreferencesEnabled': True
            }
        }
    ],

    # Retention configuration
    retentionConfig={
        'defaultRetentionDays': 365,
        'semanticRetentionDays': 730,  # 2 years for facts
        'episodicRetentionDays': 180,   # 6 months for episodes
        'preferencesRetentionDays': 365
    },

    # Encryption
    encryptionConfig={
        'kmsKeyArn': 'arn:aws:kms:us-east-1:123456789012:key/my-key'
    },

    tags=[
        {'Key': 'Project', 'Value': 'CustomerSupport'},
        {'Key': 'Environment', 'Value': 'Production'}
    ]
)

memory_store_id = response['memoryStoreId']
print(f"Memory store created: {memory_store_id}")