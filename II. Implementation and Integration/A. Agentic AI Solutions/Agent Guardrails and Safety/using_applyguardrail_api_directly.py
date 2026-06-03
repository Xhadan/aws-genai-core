import boto3

bedrock_runtime = boto3.client('bedrock-runtime')

def apply_guardrail(guardrail_id: str, version: str, content: str, source: str = 'INPUT'):
    """Apply guardrail to arbitrary content."""

    response = bedrock_runtime.apply_guardrail(
        guardrailIdentifier=guardrail_id,
        guardrailVersion=version,
        source=source,  # 'INPUT' or 'OUTPUT'
        content=[
            {
                'text': {
                    'text': content
                }
            }
        ]
    )

    return {
        'action': response['action'],  # 'NONE', 'GUARDRAIL_INTERVENED'
        'outputs': response.get('outputs', []),
        'assessments': response.get('assessments', [])
    }


def validate_tool_output(guardrail_id: str, version: str, tool_result: str):
    """Validate tool output before returning to agent."""

    result = apply_guardrail(
        guardrail_id=guardrail_id,
        version=version,
        content=tool_result,
        source='OUTPUT'
    )

    if result['action'] = 'GUARDRAIL_INTERVENED':
        # Log the intervention
        print(f"Guardrail blocked tool output")
        for assessment in result['assessments']:
            if 'sensitiveInformationPolicy' in assessment:
                for finding in assessment['sensitiveInformationPolicy'].get('piiEntities', []):
                    print(f"  - PII detected: {finding['type']}")

        # Return sanitized output
        if result['outputs']:
            return result['outputs'][0]['text']
        else:
            return "Content filtered for safety"

    return tool_result


# Example: Filter tool output
tool_output = "Customer John Smith, SSN 123-45-6789, ordered product X"
safe_output = validate_tool_output('guardrail-123', '1', tool_output)
print(f"Safe output: {safe_output}")
# Output: "Customer [NAME], SSN [US_SOCIAL_SECURITY_NUMBER], ordered product X"