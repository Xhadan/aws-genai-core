# Full RAG with metadata filtering
response = bedrock_agent_runtime.retrieve_and_generate(
    input={'text': "Summarize our security compliance requirements"},
    retrieveAndGenerateConfiguration={
        'type': 'KNOWLEDGE_BASE',
        'knowledgeBaseConfiguration': {
            'knowledgeBaseId': 'KB12345678',
            'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0',
            'retrievalConfiguration': {
                'vectorSearchConfiguration': {
                    'numberOfResults': 5,
                    'overrideSearchType': 'HYBRID',
                    'filter': {
                        'andAll': [
                            {'equals': {'key': 'category', 'value': 'compliance'}},
                            {'equals': {'key': 'is_current', 'value': True}}
                        ]
                    }
                }
            }
        }
    }
)

print(response['output']['text'])