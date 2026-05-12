import boto3
import json

bedrock = boto3.client('bedrock-runtime')

def get_embedding(text):
    """Generate embedding using Titan."""
    response = bedrock.invoke_model(
        modelId='amazon.titan-embed-text-v2:0',
        body=json.dumps({
            'inputText': text,
            'dimensions': 1024,
            'normalize': True
        })
    )
    return json.loads(response['body'].read())['embedding']

# Index a document
doc = {
    'embedding': get_embedding("Amazon Bedrock provides foundation models."),
    'text': "Amazon Bedrock provides foundation models.",
    'metadata': {
        'source': 'aws-docs',
        'category': 'ai-ml',
        'date': '2024-01-15'
    }
}

client.index(index='rag-vectors', body=doc, id='doc-001')

# Search for similar documents
query_embedding = get_embedding("What is Bedrock?")

search_query = {
    "size": 5,
    "query": {
        "knn": {
            "embedding": {
                "vector": query_embedding,
                "k": 5
            }
        }
    },
    "_source": ["text", "metadata"]
}

results = client.search(index='rag-vectors', body=search_query)

for hit in results['hits']['hits']:
    print(f"Score: {hit['_score']:.4f}")
    print(f"Text: {hit['_source']['text']}")
    print(f"Source: {hit['_source']['metadata']['source']}")