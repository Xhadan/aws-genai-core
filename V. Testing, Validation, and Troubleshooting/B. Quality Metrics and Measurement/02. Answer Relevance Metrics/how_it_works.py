import boto3
import json
import numpy as np
from typing import List, Dict

bedrock_runtime = boto3.client('bedrock-runtime')

def generate_hypothetical_questions(answer: str, n: int = 3) -> List[str]:
    """Generate questions that would be answered by this response."""

    prompt = f"""Given this answer, generate {n} different questions that this answer would directly address.
The questions should be natural and varied in phrasing.

Answer: {answer}

Return as JSON array:
["question 1", "question 2", "question 3"]
"""

    result = bedrock_runtime.converse(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        messages=[{'role': 'user', 'content': [{'text': prompt}]}],
        inferenceConfig={'maxTokens': 500, 'temperature': 0.7}  # Some creativity
    )

    return json.loads(result['output']['message']['content'][0]['text'])

def get_embedding(text: str) -> List[float]:
    """Get embedding using Titan Embeddings."""

    response = bedrock_runtime.invoke_model(
        modelId='amazon.titan-embed-text-v2:0',
        body=json.dumps({'inputText': text})
    )

    result = json.loads(response['body'].read())
    return result['embedding']

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def calculate_answer_relevance(question: str, answer: str) -> Dict:
    """Calculate answer relevance using hypothetical question generation."""

    # Generate hypothetical questions from the answer
    hypothetical_questions = generate_hypothetical_questions(answer)

    # Get embedding of original question
    original_embedding = get_embedding(question)

    # Calculate similarity for each hypothetical question
    similarities = []
    for hyp_q in hypothetical_questions:
        hyp_embedding = get_embedding(hyp_q)
        sim = cosine_similarity(original_embedding, hyp_embedding)
        similarities.append({
            'hypothetical_question': hyp_q,
            'similarity': sim
        })

    # Average similarity is the relevance score
    relevance_score = np.mean([s['similarity'] for s in similarities])

    return {
        'relevance_score': float(relevance_score),
        'hypothetical_questions': similarities,
        'original_question': question,
        'answer_length': len(answer.split())
    }

# Example usage
question = "How do I enable versioning on an S3 bucket?"
answer = """To enable versioning on an S3 bucket:
1. Go to the S3 console and select your bucket
2. Click on the Properties tab
3. Find the Bucket Versioning section
4. Click Edit and select Enable
5. Save changes

You can also use the AWS CLI:
aws s3api put-bucket-versioning --bucket my-bucket --versioning-configuration Status=Enabled
"""

result = calculate_answer_relevance(question, answer)
print(f"Relevance Score: {result['relevance_score']:.3f}")