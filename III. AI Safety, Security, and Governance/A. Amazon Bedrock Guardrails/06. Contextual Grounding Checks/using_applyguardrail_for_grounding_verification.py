import boto3

bedrock_runtime = boto3.client('bedrock-runtime')

def verify_grounding(
    query,
    source_context,
    response_text,
    guardrail_id,
    guardrail_version
):
    """
    Verify response grounding against source context using ApplyGuardrail.
    """
    # Format content with grounding context
    # The guardrail evaluates the response against the provided context
    content = [
        {
            'text': {
                'text': response_text,
                'qualifiers': ['query']  # This is the response to evaluate
            }
        }
    ]

    # Provide grounding sources
    grounding_source = {
        'text': source_context
    }

    response = bedrock_runtime.apply_guardrail(
        guardrailIdentifier=guardrail_id,
        guardrailVersion=guardrail_version,
        source='OUTPUT',  # Evaluating model output
        content=content,
        groundingSource=grounding_source
    )

    result = {
        'action': response['action'],
        'grounding_passed': response['action'] != 'GUARDRAIL_INTERVENED',
        'scores': {}
    }

    # Extract detailed scores
    for assessment in response.get('assessments', []):
        grounding = assessment.get('contextualGroundingPolicy', {})
        for filter_result in grounding.get('filters', []):
            result['scores'][filter_result['type'].lower()] = {
                'score': filter_result.get('score'),
                'threshold': filter_result.get('threshold'),
                'action': filter_result.get('action')
            }

    return result

# Verify a response
source_docs = """
Our return policy allows returns within 30 days of purchase.
Electronics must be unopened for full refund.
Opened electronics may be exchanged within 14 days.
"""

model_response = """
You can return electronics within 30 days for a full refund.
If the item is opened, you have 14 days for an exchange.
We also offer a 90-day warranty on all electronics.
"""  # Note: 90-day warranty is NOT in source - potential hallucination

result = verify_grounding(
    query="What is the return policy?",
    source_context=source_docs,
    response_text=model_response,
    guardrail_id="your-guardrail-id",
    guardrail_version="1"
)

print(f"Grounding Passed: {result['grounding_passed']}")
for score_type, details in result['scores'].items():
    print(f"  {score_type}: {details['score']:.2f} (threshold: {details['threshold']})")