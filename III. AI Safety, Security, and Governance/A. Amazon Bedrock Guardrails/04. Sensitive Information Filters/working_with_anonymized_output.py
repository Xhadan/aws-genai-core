import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime')

def process_with_pii_handling(prompt, guardrail_id, guardrail_version):
    """
    Process prompt with PII anonymization and extract details.
    """
    response = bedrock_runtime.apply_guardrail(
        guardrailIdentifier=guardrail_id,
        guardrailVersion=guardrail_version,
        source='INPUT',
        content=[{'text': {'text': prompt}}]
    )

    result = {
        'action': response['action'],
        'original_prompt': prompt,
        'processed_prompt': None,
        'pii_detected': []
    }

    if response['action'] = 'GUARDRAIL_INTERVENED':
        # Check if anonymized (outputs present) or blocked (no outputs)
        if response.get('outputs'):
            # Anonymized - use the masked version
            result['processed_prompt'] = response['outputs'][0]['text']
        else:
            # Blocked entirely
            result['processed_prompt'] = None

    else:
        # No intervention - use original
        result['processed_prompt'] = prompt

    # Extract PII detection details from assessments
    for assessment in response.get('assessments', []):
        sensitive_info = assessment.get('sensitiveInformationPolicy', {})
        for pii_entity in sensitive_info.get('piiEntities', []):
            result['pii_detected'].append({
                'type': pii_entity.get('type'),
                'action': pii_entity.get('action'),
                'match': pii_entity.get('match')
            })
        for regex_match in sensitive_info.get('regexes', []):
            result['pii_detected'].append({
                'type': regex_match.get('name'),
                'action': regex_match.get('action'),
                'match': regex_match.get('match')
            })

    return result

# Test with PII-containing prompt
test_prompt = """
Hi, I'm John Smith and my email is john.smith@example.com.
My SSN is 123-45-6789 and my employee ID is EMP123456.
Can you help me with my account?
"""

result = process_with_pii_handling(test_prompt, 'your-guardrail-id', '1')

print(f"Action: {result['action']}")
print(f"PII Detected: {len(result['pii_detected'])} entities")
for pii in result['pii_detected']:
    print(f"  - {pii['type']}: {pii['action']}")

if result['processed_prompt']:
    print(f"\nProcessed prompt:\n{result['processed_prompt']}")
    # Output might be:
    # Hi, I'm {NAME} and my email is {EMAIL}.
    # [BLOCKED - SSN detected]
    # My employee ID is {EMPLOYEE_ID}.
    # Can you help me with my account?