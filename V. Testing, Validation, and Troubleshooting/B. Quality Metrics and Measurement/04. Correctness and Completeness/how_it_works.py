import boto3
import json
import numpy as np
from typing import Dict, List

bedrock_runtime = boto3.client('bedrock-runtime')

def get_embedding(text: str) -> List[float]:
    """Get embedding for text."""
    response = bedrock_runtime.invoke_model(
        modelId='amazon.titan-embed-text-v2:0',
        body=json.dumps({'inputText': text})
    )
    return json.loads(response['body'].read())['embedding']

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity."""
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def extract_facts(text: str) -> List[str]:
    """Extract atomic facts from text."""
    prompt = f"""Extract all distinct factual claims from this text.
Each fact should be a single, verifiable statement.

Text: {text}

Return as JSON array of strings.
"""
    result = bedrock_runtime.converse(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        messages=[{'role': 'user', 'content': [{'text': prompt}]}],
        inferenceConfig={'maxTokens': 1000, 'temperature': 0.0}
    )
    return json.loads(result['output']['message']['content'][0]['text'])

def calculate_factual_f1(response_facts: List[str], ground_truth_facts: List[str]) -> Dict:
    """Calculate F1 score for factual overlap."""

    # Check which response facts match ground truth
    matches = 0
    for r_fact in response_facts:
        r_embed = get_embedding(r_fact)
        for gt_fact in ground_truth_facts:
            gt_embed = get_embedding(gt_fact)
            if cosine_similarity(r_embed, gt_embed) > 0.85:  # Threshold
                matches += 1
                break

    precision = matches / len(response_facts) if response_facts else 0
    recall = matches / len(ground_truth_facts) if ground_truth_facts else 0

    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'matched_facts': matches,
        'response_facts': len(response_facts),
        'ground_truth_facts': len(ground_truth_facts)
    }

def evaluate_correctness(response: str, ground_truth: str) -> Dict:
    """Comprehensive correctness evaluation."""

    # Semantic similarity
    response_embed = get_embedding(response)
    gt_embed = get_embedding(ground_truth)
    semantic_sim = cosine_similarity(response_embed, gt_embed)

    # Factual F1
    response_facts = extract_facts(response)
    gt_facts = extract_facts(ground_truth)
    factual_result = calculate_factual_f1(response_facts, gt_facts)

    # Combined score
    correctness = 0.5 * semantic_sim + 0.5 * factual_result['f1_score']

    return {
        'correctness_score': correctness,
        'semantic_similarity': semantic_sim,
        'factual_f1': factual_result['f1_score'],
        'factual_precision': factual_result['precision'],
        'factual_recall': factual_result['recall'],
        'details': factual_result
    }

# Example usage
ground_truth = """Amazon S3 provides 99.999999999% (11 nines) durability.
It stores data across at least 3 Availability Zones.
S3 Standard offers 99.99% availability SLA."""

response = """S3 offers extremely high durability of 11 nines (99.999999999%).
Data is replicated across multiple AZs for protection.
The availability SLA for S3 Standard is 99.99%."""

result = evaluate_correctness(response, ground_truth)
print(f"Correctness Score: {result['correctness_score']:.3f}")
print(f"Semantic Similarity: {result['semantic_similarity']:.3f}")
print(f"Factual F1: {result['factual_f1']:.3f}")