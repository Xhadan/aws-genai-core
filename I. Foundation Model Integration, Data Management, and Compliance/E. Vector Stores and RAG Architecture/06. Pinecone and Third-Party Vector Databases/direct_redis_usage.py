import redis
from redis.commands.search.field import VectorField, TextField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import numpy as np
import boto3
import json

# Connect to Redis Enterprise
r = redis.Redis(
    host='redis-12345.c1.us-east-1-1.ec2.cloud.redislabs.com',
    port345,
    password='your-password',
    decode_responses=True
)

# Create vector search index
schema = [
    TextField('content'),
    TagField('category'),
    VectorField('embedding',
        'HNSW',
        {
            'TYPE': 'FLOAT32',
            'DIM': 1024,
            'DISTANCE_METRIC': 'COSINE',
            'M': 16,
            'EF_CONSTRUCTION': 200
        }
    )
]

r.ft('rag_index').create_index(
    schema,
    definition=IndexDefinition(prefix=['doc:'], index_type=IndexType.HASH)
)

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

# Store document
embedding = get_embedding('Amazon Bedrock provides foundation models.')
r.hset('doc:001', mapping={
    'content': 'Amazon Bedrock provides foundation models.',
    'category': 'ai-ml',
    'embedding': np.array(embedding, dtype=np.float32).tobytes()
})

# Vector search
query_embedding = get_embedding('What is Bedrock?')
query_vector = np.array(query_embedding, dtype=np.float32).tobytes()

q = Query(
    f'(@category:{{ai-ml}})=>[KNN 5 @embedding $vec AS score]'
).sort_by('score').return_fields('content', 'category', 'score').dialect(2)

results = r.ft('rag_index').search(q, query_params={'vec': query_vector})

for doc in results.docs:
    print(f"Score: {doc.score}, Content: {doc.content[:100]}")