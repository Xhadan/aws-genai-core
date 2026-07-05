import boto3

bedrock_runtime = boto3.client('bedrock-runtime')

def process_with_retry(prompt, guardrail_id, guardrail_version, max_retries=3):
    """
    Process with ARC, retry with violation feedback if needed.
    """
    additional_context = ""

    for attempt in range(max_retries):
        # Include violation feedback in retry
        full_prompt = prompt
        if additional_context:
            full_prompt = f"{prompt}\n\nIMPORTANT: {additional_context}"

        response = bedrock_runtime.converse(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            messages=[
                {'role': 'user', 'content': [{'text': full_prompt}]}
            ],
            guardrailConfig={
                'guardrailIdentifier': guardrail_id,
                'guardrailVersion': guardrail_version,
                'trace': 'enabled'
            }
        )

        if response.get('stopReason') != 'guardrail_intervened':
            # Success - compliant response
            return {
                'success': True,
                'response': response['output']['message']['content'][0]['text'],
                'attempts': attempt + 1
            }

        # Extract violation details for retry guidance
        trace = response.get('trace', {}).get('guardrail', {})
        arc = trace.get('outputAssessment', {}).get('automatedReasoningPolicy', {})

        violations = []
        for finding in arc.get('findings', []):
            violations.append(finding.get('recommendation', finding.get('reason')))

        additional_context = "Ensure your response: " + "; ".join(violations)

    return {
        'success': False,
        'response': None,
        'attempts': max_retries,
        'last_violations': violations
    }