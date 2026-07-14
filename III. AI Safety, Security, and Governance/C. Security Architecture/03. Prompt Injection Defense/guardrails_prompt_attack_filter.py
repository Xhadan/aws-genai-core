import boto3

bedrock = boto3.client('bedrock')

def create_injection_protected_guardrail():
    """
    Create guardrail with prompt injection protection.
    """
    response = bedrock.create_guardrail(
        name='prompt-injection-protection',
        description='Protects against prompt injection attacks',

        contentPolicyConfig={
            'filtersConfig': [
                # PROMPT_ATTACK is INPUT-only
                {
                    'type': 'PROMPT_ATTACK',
                    'inputStrength': 'HIGH',  # Aggressive detection
                    'outputStrength': 'NONE'  # No effect on output
                },
                # Also enable other content filters
                {'type': 'MISCONDUCT', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                {'type': 'HATE', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                {'type': 'VIOLENCE', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'}
            ]
        },

        blockedInputMessaging='Your request could not be processed due to security policies.',
        blockedOutputsMessaging='Response blocked for safety reasons.'
    )

    return response['guardrailId']

guardrail_id = create_injection_protected_guardrail()
print(f"Created guardrail: {guardrail_id}")