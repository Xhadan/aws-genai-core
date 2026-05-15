import boto3

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

# Simple equality filter
response = bedrock_agent_runtime.retrieve(
    knowledgeBaseId='KB12345678',
    retrievalQuery={'text': "What is the vacation policy?"},
    retrievalConfiguration={
        'vectorSearchConfiguration': {
            'numberOfResults': 5,
            'overrideSearchType': 'HYBRID',
            'filter': {
                'equals': {
                    'key': 'category',
                    'value': 'policy'
                }
            }
        }
    }
)

# Multiple conditions with AND
response = bedrock_agent_runtime.retrieve(
    knowledgeBaseId='KB12345678',
    retrievalQuery={'text': "Employee benefits overview"},
    retrievalConfiguration={
        'vectorSearchConfiguration': {
            'numberOfResults': 10,
            'filter': {
                'andAll': [
                    {
                        'equals': {
                            'key': 'department',
                            'value': 'human-resources'
                        }
                    },
                    {
                        'equals': {
                            'key': 'is_current',
                            'value': True
                        }
                    }
                ]
            }
        }
    }
)

# OR conditions
response = bedrock_agent_runtime.retrieve(
    knowledgeBaseId='KB12345678',
    retrievalQuery={'text': "Security guidelines"},
    retrievalConfiguration={
        'vectorSearchConfiguration': {
            'numberOfResults': 5,
            'filter': {
                'orAll': [
                    {'equals': {'key': 'category', 'value': 'security'}},
                    {'equals': {'key': 'category', 'value': 'compliance'}}
                ]
            }
        }
    }
)