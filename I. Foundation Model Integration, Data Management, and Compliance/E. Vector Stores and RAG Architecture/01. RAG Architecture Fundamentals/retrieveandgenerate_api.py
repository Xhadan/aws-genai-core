# Simpler approach using combined API
response = bedrock_agent_runtime.retrieve_and_generate(
    input={'text': "What are the compliance requirements for data retention?"},
    retrieveAndGenerateConfiguration={
        'type': 'KNOWLEDGE_BASE',
        'knowledgeBaseConfiguration': {
            'knowledgeBaseId': 'KB12345678',
            'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0',
            'retrievalConfiguration': {
                'vectorSearchConfiguration': {
                    'numberOfResults': 5
                }
            },
            'generationConfiguration': {
                'inferenceConfig': {
                    'textInferenceConfig': {
                        'maxTokens': 1024,
                        'temperature': 0.0
                    }
                }
            }
        }
    }
)

print(response['output']['text'])
# Citations automatically included
for citation in response.get('citations', []):
    print(f"Source: {citation['retrievedReferences'][0]['location']}")