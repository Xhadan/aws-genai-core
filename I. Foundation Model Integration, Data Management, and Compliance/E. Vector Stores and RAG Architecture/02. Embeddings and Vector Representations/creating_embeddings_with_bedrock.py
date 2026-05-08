import boto3
import json

bedrock = boto3.client('bedrock-runtime')

def get_embedding(text, model_id="amazon.titan-embed-text-v2:0"):
    """Generate embedding vector for text."""
    response = bedrock.invoke_model(
        modelId=model_id,
        body=json.dumps({
            "inputText": text,
            "dimensions": 1024,  # V2 supports 256, 512, 1024
            "normalize": True    # Normalize for cosine similarity
        })
    )
    result = json.loads(response['body'].read())
    return result['embedding']

# Example
text = "Amazon Bedrock is a fully managed service for foundation models."
embedding = get_embedding(text)
print(f"Embedding dimensions: {len(embedding)}")  # 1024
print(f"First 5 values: {embedding[:5]}")