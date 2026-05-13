from pinecone import Pinecone, ServerlessSpec
import boto3
import json

# Initialize Pinecone
pc = Pinecone(api_key='your-api-key')

# Create serverless index
pc.create_index(
    name='rag-embeddings',
    dimension24,  # Match Titan Embeddings V2
    metric='cosine',
    spec=ServerlessSpec(
        cloud='aws',
        region='us-east-1'
    )
)

index = pc.Index('rag-embeddings')

# Bedrock client for embeddings
bedrock = boto3.client('bedrock-runtime')

def get_embedding(text):
    response = bedrock.invoke_model(
        modelId='amazon.titan-embed-text-v2:0',
        body=json.dumps({
            'inputText': text,
            'dimensions': 1024,
            'normalize': True
        })
    )
    return json.loads(response['body'].read())['embedding']

# Upsert vectors with metadata
vectors = [
    {
        'id': 'doc-001-chunk-0',
        'values': get_embedding("Amazon Bedrock provides foundation models."),
        'metadata': {
            'source': 'aws-docs',
            'category': 'ai-ml',
            'document_id': 'doc-001',
            'chunk_index': 0
        }
    }
]

index.upsert(vectors=vectors, namespace='documents')

# Query with metadata filter
results = index.query(
    vector=get_embedding("What is Bedrock?"),
    top_k=5,
    namespace='documents',
    filter={
        'category': {'$eq': 'ai-ml'}
    },
    include_metadata=True
)

for match in results['matches']:
    print(f"Score: {match['score']:.4f}, ID: {match['id']}")