import boto3

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

# Query with hybrid search enabled
response = bedrock_agent_runtime.retrieve(
    knowledgeBaseId='KB12345678',
    retrievalQuery={'text': "What is the ARN format for Lambda functions?"},
    retrievalConfiguration={
        'vectorSearchConfiguration': {
            'numberOfResults': 10,
            'overrideSearchType': 'HYBRID'  # Enable hybrid search
        }
    }
)

for result in response['retrievalResults']:
    print(f"Score: {result['score']:.4f}")
    print(f"Content: {result['content']['text'][:200]}...")
    print("---")