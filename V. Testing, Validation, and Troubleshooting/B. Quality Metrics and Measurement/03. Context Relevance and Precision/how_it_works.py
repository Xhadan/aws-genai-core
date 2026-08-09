import boto3
import json
from typing import List, Dict

bedrock_runtime = boto3.client('bedrock-runtime')
bedrock_agent = boto3.client('bedrock-agent-runtime')

def retrieve_from_knowledge_base(
    question: str,
    kb_id: str,
    num_results: int = 5
) -> List[Dict]:
    """Retrieve chunks from Bedrock Knowledge Base."""

    response = bedrock_agent.retrieve(
        knowledgeBaseId=kb_id,
        retrievalQuery={'text': question},
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': num_results
            }
        }
    )

    return [
        {
            'content': r['content']['text'],
            'score': r['score'],
            'source': r.get('location', {}).get('s3Location', {}).get('uri', '')
        }
        for r in response['retrievalResults']
    ]

def evaluate_chunk_relevance(
    question: str,
    chunk: str
) -> Dict:
    """Evaluate if a chunk is relevant to the question."""

    prompt = f"""Determine if this text chunk is relevant for answering the question.

Question: {question}

Chunk: {chunk}

Consider:
- Does the chunk contain information that helps answer the question?
- Is the information directly related or just tangentially related?

Return JSON:
{{
    "relevant": true/false,
    "relevance_score": 0.0-1.0,
    "reasoning": "brief explanation"
}}
"""

    result = bedrock_runtime.converse(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        messages=[{'role': 'user', 'content': [{'text': prompt}]}],
        inferenceConfig={'maxTokens': 200, 'temperature': 0.0}
    )

    return json.loads(result['output']['message']['content'][0]['text'])

def calculate_context_precision(
    question: str,
    retrieved_chunks: List[Dict]
) -> Dict:
    """Calculate context precision for retrieved chunks."""

    evaluations = []
    relevant_count = 0
    weighted_sum = 0
    relevance_sum = 0

    for i, chunk in enumerate(retrieved_chunks):
        eval_result = evaluate_chunk_relevance(question, chunk['content'])
        eval_result['position'] = i + 1
        eval_result['retrieval_score'] = chunk['score']
        evaluations.append(eval_result)

        if eval_result['relevant']:
            relevant_count += 1
            # Position weight for weighted precision
            position_weight = 1.0 / (i + 1)
            weighted_sum += position_weight
            relevance_sum += position_weight

    # Standard precision
    precision = relevant_count / len(retrieved_chunks) if retrieved_chunks else 0

    # Weighted precision (by position)
    total_possible_weight = sum(1.0 / (i + 1) for i in range(len(retrieved_chunks)))
    weighted_precision = weighted_sum / total_possible_weight if total_possible_weight > 0 else 0

    return {
        'context_precision': precision,
        'weighted_precision': weighted_precision,
        'relevant_chunks': relevant_count,
        'total_chunks': len(retrieved_chunks),
        'chunk_evaluations': evaluations
    }

# Example usage
question = "How do I configure S3 bucket encryption?"
kb_id = "KNOWLEDGE_BASE_ID"

chunks = retrieve_from_knowledge_base(question, kb_id, num_results=5)
precision_result = calculate_context_precision(question, chunks)

print(f"Context Precision: {precision_result['context_precision']:.2f}")
print(f"Weighted Precision: {precision_result['weighted_precision']:.2f}")
print(f"Relevant Chunks: {precision_result['relevant_chunks']}/{precision_result['total_chunks']}")