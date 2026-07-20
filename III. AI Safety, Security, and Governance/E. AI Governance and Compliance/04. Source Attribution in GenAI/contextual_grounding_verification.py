import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime')
bedrock = boto3.client('bedrock')

def create_grounding_guardrail(
    guardrail_name: str,
    grounding_threshold: float = 0.7,
    relevance_threshold: float = 0.5
) -> str:
    """
    Create guardrail with contextual grounding checks.
    """
    response = bedrock.create_guardrail(
        name=guardrail_name,
        description='Guardrail with contextual grounding verification',
        contextualGroundingPolicyConfig={
            'filtersConfig': [
                {
                    'type': 'GROUNDING',
                    'threshold': grounding_threshold
                },
                {
                    'type': 'RELEVANCE',
                    'threshold': relevance_threshold
                }
            ]
        },
        blockedInputMessaging='Request could not be processed.',
        blockedOutputsMessaging='Response blocked due to insufficient grounding in sources.'
    )

    print(f"Grounding guardrail created: {response['guardrailId']}")
    return response['guardrailId']


def invoke_with_grounding_check(
    model_id: str,
    prompt: str,
    grounding_source: str,
    guardrail_id: str
) -> Dict:
    """
    Invoke model with contextual grounding check.
    grounding_source is the retrieved context that should ground the response.
    """
    # Build prompt with context
    full_prompt = f"""Answer the following question using ONLY the information provided in the context below.
If the answer cannot be found in the context, say "I don't have enough information to answer that."

Context:
{grounding_source}

Question: {prompt}

Answer:"""

    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        guardrailIdentifier=guardrail_id,
        guardrailVersion='DRAFT',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 1000,
            'messages': [{'role': 'user', 'content': full_prompt}]
        })
    )

    result = json.loads(response['body'].read())

    # Check guardrail action
    guardrail_action = response.get('ResponseMetadata', {}).get('HTTPHeaders', {}).get('x-amzn-guardrail-action', 'none')

    return {
        'response': result.get('content', [{}])[0].get('text', ''),
        'guardrail_action': guardrail_action,
        'grounded': guardrail_action != 'BLOCKED'
    }


def verify_claim_grounding(
    claims: List[str],
    sources: List[str],
    model_id: str
) -> List[Dict]:
    """
    Verify each claim is grounded in sources.
    Uses the model to check grounding (for custom verification).
    """
    verification_results = []

    for claim in claims:
        verification_prompt = f"""Verify if the following claim is supported by the given sources.

Claim: {claim}

Sources:
{chr(10).join([f'- {s}' for s in sources])}

Is this claim fully supported by the sources? Respond with:
- SUPPORTED: If the claim is directly stated or clearly implied in the sources
- PARTIAL: If only part of the claim is supported
- NOT_SUPPORTED: If the claim cannot be verified from the sources

Also explain your reasoning briefly."""

        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 500,
                'messages': [{'role': 'user', 'content': verification_prompt}]
            })
        )

        result = json.loads(response['body'].read())
        verification_text = result.get('content', [{}])[0].get('text', '')

        # Parse result
        grounding_status = 'UNKNOWN'
        if 'SUPPORTED' in verification_text.upper()[:50]:
            grounding_status = 'SUPPORTED'
        elif 'PARTIAL' in verification_text.upper()[:50]:
            grounding_status = 'PARTIAL'
        elif 'NOT_SUPPORTED' in verification_text.upper()[:50]:
            grounding_status = 'NOT_SUPPORTED'

        verification_results.append({
            'claim': claim,
            'grounding_status': grounding_status,
            'explanation': verification_text
        })

    return verification_results


# Example: Create grounding guardrail
guardrail_id = create_grounding_guardrail(
    guardrail_name='rag-grounding-guardrail',
    grounding_threshold=0.7,
    relevance_threshold=0.5
)

# Example: Verify grounding
context = """
Our return policy allows returns within 30 days for electronics.
Items must be in original packaging with receipt.
Opened software cannot be returned.
"""

result = invoke_with_grounding_check(
    model_id='anthropic.claude-3-sonnet-20240229-v1:0',
    prompt='What is the return window for electronics?',
    grounding_source=context,
    guardrail_id=guardrail_id
)

print(f"Response: {result['response']}")
print(f"Grounded: {result['grounded']}")