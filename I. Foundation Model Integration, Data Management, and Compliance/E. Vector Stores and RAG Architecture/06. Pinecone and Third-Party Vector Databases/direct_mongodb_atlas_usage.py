from pymongo import MongoClient
import boto3
import json

# Connect to MongoDB Atlas
client = MongoClient('mongodb+srv://user:password@cluster.abc123.mongodb.net/')
db = client['rag_database']
collection = db['document_chunks']

# Create vector search index (run once)
# Use Atlas UI or API to create this index:
# {
#   "fields": [
#     {
#       "type": "vector",
#       "path": "embedding",
#       "numDimensions": 1024,
#       "similarity": "cosine"
#     }
#   ]
# }

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

# Insert document with embedding
doc = {
    'document_id': 'doc-001',
    'chunk_index': 0,
    'content': 'Amazon Bedrock provides foundation models.',
    'embedding': get_embedding('Amazon Bedrock provides foundation models.'),
    'metadata': {
        'source': 'aws-docs',
        'category': 'ai-ml',
        'date': '2024-01-15'
    }
}
collection.insert_one(doc)

# Vector search with aggregation pipeline
pipeline = [
    {
        '$vectorSearch': {
            'index': 'vector_index',
            'path': 'embedding',
            'queryVector': get_embedding('What is Bedrock?'),
            'numCandidates': 100,
            'limit': 5
        }
    },
    {
        '$match': {
            'metadata.category': 'ai-ml'
        }
    },
    {
        '$project': {
            'content': 1,
            'metadata': 1,
            'score': {'$meta': 'vectorSearchScore'}
        }
    }
]

results = collection.aggregate(pipeline)
for doc in results:
    print(f"Score: {doc['score']:.4f}, Content: {doc['content'][:100]}")