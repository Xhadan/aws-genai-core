import boto3
import json

bedrock = boto3.client('bedrock-runtime')

def get_embeddings(text, dimensions24):
    """Generate embeddings with configurable dimensions."""
    response = bedrock.invoke_model(
        modelId='amazon.titan-embed-text-v2:0',
        body=json.dumps({
            'inputText': text,
            'dimensions': dimensions,  # 256, 512, or 1024
            'normalize': True
        })
    )

    result = json.loads(response['body'].read())
    return result['embedding']

# Generate embeddings for RAG
document_embedding = get_embeddings(
    "Amazon Bedrock is a fully managed service...",
    dimensions24  # Maximum accuracy
)

# Generate query embedding (matching dimensions)
query_embedding = get_embeddings(
    "What is Amazon Bedrock?",
    dimensions24
)