import boto3

bedrock_runtime = boto3.client('bedrock-runtime')

# Evaluate text content without model invocation
def evaluate_with_guardrail(text, guardrail_id, guardrail_version, source='INPUT'):
    """
    Apply guardrail to any text content.
    source: 'INPUT' for user prompts, 'OUTPUT' for model responses
    """
    response = bedrock_runtime.apply_guardrail(
        guardrailIdentifier=guardrail_id,
        guardrailVersion=guardrail_version,
        source=source,
        content=[
            {'text': {'text': text}}
        ]
    )

    return {
        'action': response['action'],  # GUARDRAIL_INTERVENED or NONE
        'outputs': response.get('outputs', []),
        'assessments': response.get('assessments', [])
    }

# Example: Pre-screen user input before external model
user_input = "My SSN is 123-45-6789. Can you help me?"
result = evaluate_with_guardrail(
    text=user_input,
    guardrail_id='abc123',
    guardrail_version='1',
    source='INPUT'
)

if result['action'] = 'GUARDRAIL_INTERVENED':
    print("Input blocked or modified by guardrail")
    # Use anonymized output if available
    if result['outputs']:
        safe_input = result['outputs'][0]['text']
        print(f"Anonymized input: {safe_input}")
else:
    print("Input passed guardrail checks")
    # Proceed to send to external model