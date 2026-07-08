import boto3

bedrock_runtime = boto3.client('bedrock-runtime')

def anonymize_with_guardrails(text, guardrail_id, guardrail_version):
    """
    Use Guardrails ANONYMIZE action for runtime masking.
    """
    response = bedrock_runtime.apply_guardrail(
        guardrailIdentifier=guardrail_id,
        guardrailVersion=guardrail_version,
        source='INPUT',
        content=[{'text': {'text': text}}]
    )

    if response['action'] = 'GUARDRAIL_INTERVENED' and response.get('outputs'):
        return {
            'success': True,
            'anonymized_text': response['outputs'][0]['text'],
            'original_text': text
        }
    elif response['action'] = 'NONE':
        return {
            'success': True,
            'anonymized_text': text,  # No PII found
            'original_text': text
        }
    else:
        return {
            'success': False,
            'blocked': True,
            'original_text': text
        }

# Example
text = "Contact John Smith at john@company.com or (555) 123-4567"
result = anonymize_with_guardrails(text, 'guardrail-id', '1')

if result['success']:
    print(f"Anonymized: {result['anonymized_text']}")
    # Output: Contact {NAME} at {EMAIL} or {PHONE}