import boto3
import json
from typing import List, Dict

bedrock_runtime = boto3.client('bedrock-runtime')

def extract_claims(response: str) -> List[str]:
    """Extract atomic claims from a response using LLM."""

    prompt = f"""Extract all atomic factual claims from the following text.
Each claim should be a single, verifiable statement.

Text: {response}

Return claims as a JSON array of strings:
["claim 1", "claim 2", ...]
"""

    result = bedrock_runtime.converse(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        messages=[{'role': 'user', 'content': [{'text': prompt}]}],
        inferenceConfig={'maxTokens': 1000, 'temperature': 0.0}
    )

    claims_text = result['output']['message']['content'][0]['text']
    return json.loads(claims_text)

def verify_claim(claim: str, context: str) -> Dict:
    """Verify if a claim is supported by the context."""

    prompt = f"""Determine if the following claim is supported by the context.

Context: {context}

Claim: {claim}

Respond with JSON:
{{
    "verdict": "supported" | "contradicted" | "not_mentioned",
    "evidence": "quote from context if supported, otherwise null",
    "confidence": 0.0 to 1.0
}}
"""

    result = bedrock_runtime.converse(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        messages=[{'role': 'user', 'content': [{'text': prompt}]}],
        inferenceConfig={'maxTokens': 500, 'temperature': 0.0}
    )

    return json.loads(result['output']['message']['content'][0]['text'])

def calculate_faithfulness(response: str, context: str) -> Dict:
    """Calculate faithfulness score for a response."""

    # Extract claims
    claims = extract_claims(response)

    # Verify each claim
    verifications = []
    for claim in claims:
        verification = verify_claim(claim, context)
        verification['claim'] = claim
        verifications.append(verification)

    # Calculate score
    supported = sum(1 for v in verifications if v['verdict'] = 'supported')
    contradicted = sum(1 for v in verifications if v['verdict'] = 'contradicted')
    not_mentioned = sum(1 for v in verifications if v['verdict'] = 'not_mentioned')

    faithfulness_score = supported / len(claims) if claims else 0

    return {
        'faithfulness_score': faithfulness_score,
        'total_claims': len(claims),
        'supported': supported,
        'contradicted': contradicted,
        'not_mentioned': not_mentioned,
        'verifications': verifications,
        'has_hallucinations': contradicted > 0 or not_mentioned > 0
    }

# Example usage
context = """Amazon Bedrock is a fully managed service that offers a choice of
high-performing foundation models from leading AI companies like AI21 Labs,
Anthropic, Cohere, Meta, Mistral AI, Stability AI, and Amazon through a single API."""

response = """Amazon Bedrock provides access to multiple foundation models including
Claude from Anthropic, Llama from Meta, and GPT-4 from OpenAI through a unified API."""

result = calculate_faithfulness(response, context)
print(f"Faithfulness Score: {result['faithfulness_score']:.2f}")
print(f"Has Hallucinations: {result['has_hallucinations']}")
# Note: GPT-4/OpenAI is not mentioned in context - hallucination detected