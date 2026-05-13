import boto3
import json
import psycopg2
from pgvector.psycopg2 import register_vector

# Database connection
conn = psycopg2.connect(
    host='my-aurora-cluster.cluster-abc123.us-east-1.rds.amazonaws.com',
    database='ragdb',
    user='admin',
    password='your-password',
    portT32
)

# Register vector type with psycopg2
register_vector(conn)
cursor = conn.cursor()

# Bedrock client for embeddings
bedrock = boto3.client('bedrock-runtime')

def get_embedding(text):
    """Generate embedding using Titan Embeddings V2."""
    response = bedrock.invoke_model(
        modelId='amazon.titan-embed-text-v2:0',
        body=json.dumps({
            'inputText': text,
            'dimensions': 1024,
            'normalize': True
        })
    )
    return json.loads(response['body'].read())['embedding']

def store_chunk(document_id, chunk_index, content, metadata=None):
    """Store document chunk with embedding."""
    embedding = get_embedding(content)

    cursor.execute("""
        INSERT INTO document_chunks
        (document_id, chunk_index, content, embedding, metadata)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (document_id, chunk_index)
        DO UPDATE SET content = EXCLUDED.content,
                      embedding = EXCLUDED.embedding,
                      metadata = EXCLUDED.metadata
    """, (document_id, chunk_index, content, embedding,
          json.dumps(metadata) if metadata else None))

    conn.commit()

# Example: Store document chunks
chunks = [
    "Amazon Bedrock is a fully managed service for foundation models.",
    "It provides access to models from AI21, Anthropic, Cohere, and more.",
    "Bedrock supports RAG through Knowledge Bases feature."
]

for i, chunk in enumerate(chunks):
    store_chunk('doc-001', i, chunk, {'source': 'aws-docs', 'category': 'ai-ml'})