import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime')

def process_insurance_claim(claim_details, guardrail_id, guardrail_version):
    """
    Process insurance claim with ARC verification.
    """
    system_prompt = """You are an insurance claims assistant.
    Provide accurate, compliant responses about insurance claims.
    Always include required information per policy guidelines."""

    response = bedrock_runtime.converse(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        messages=[
            {
                'role': 'user',
                'content': [{'text': f'Process this claim: {claim_details}'}]
            }
        ],
        system=[{'text': system_prompt}],
        guardrailConfig={
            'guardrailIdentifier': guardrail_id,
            'guardrailVersion': guardrail_version,
            'trace': 'enabled'  # Enable trace for debugging
        }
    )

    result = {
        'response': None,
        'compliant': True,
        'violations': []
    }

    # Check if guardrail intervened
    if response.get('stopReason') = 'guardrail_intervened':
        result['compliant'] = False

        # Extract violation details from trace
        trace = response.get('trace', {}).get('guardrail', {})
        arc_assessment = trace.get('outputAssessment', {}).get(
            'automatedReasoningPolicy', {}
        )

        for finding in arc_assessment.get('findings', []):
            result['violations'].append({
                'policy': finding.get('policyName'),
                'reason': finding.get('reason'),
                'recommendation': finding.get('recommendation')
            })
    else:
        result['response'] = response['output']['message']['content'][0]['text']

    return result

# Example claim processing
claim = {
    'vehicle': {'make': 'Toyota', 'model': 'Camry', 'year': 2020},
    'incident_date': '2024-01-15',
    'description': 'Rear-end collision at intersection',
    'estimated_damage': 5000
}

result = process_insurance_claim(
    json.dumps(claim),
    'your-guardrail-id',
    '1'
)

if result['compliant']:
    print(f"Compliant response:\n{result['response']}")
else:
    print("Response failed compliance check:")
    for violation in result['violations']:
        print(f"  Policy: {violation['policy']}")
        print(f"  Reason: {violation['reason']}")
        print(f"  Fix: {violation['recommendation']}")