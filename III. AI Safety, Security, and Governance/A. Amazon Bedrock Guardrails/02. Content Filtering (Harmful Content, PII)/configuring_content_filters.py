import boto3

bedrock = boto3.client('bedrock')

# Create guardrail with content filters
response = bedrock.create_guardrail(
    name='content-filter-guardrail',
    description='Comprehensive content filtering configuration',

    contentPolicyConfig={
        'filtersConfig': [
            # Hate speech - block discriminatory content
            {
                'type': 'HATE',
                'inputStrength': 'HIGH',
                'outputStrength': 'HIGH'
            },
            # Insults - aggressive for customer-facing
            {
                'type': 'INSULTS',
                'inputStrength': 'HIGH',
                'outputStrength': 'HIGH'
            },
            # Sexual content - block explicit material
            {
                'type': 'SEXUAL',
                'inputStrength': 'HIGH',
                'outputStrength': 'HIGH'
            },
            # Violence - block graphic content
            {
                'type': 'VIOLENCE',
                'inputStrength': 'HIGH',
                'outputStrength': 'HIGH'
            },
            # Misconduct - block criminal instructions
            {
                'type': 'MISCONDUCT',
                'inputStrength': 'HIGH',
                'outputStrength': 'HIGH'
            },
            # Prompt attacks - INPUT ONLY (output setting ignored)
            {
                'type': 'PROMPT_ATTACK',
                'inputStrength': 'HIGH',
                'outputStrength': 'NONE'  # No effect, but explicit
            }
        ]
    },

    blockedInputMessaging='Your request contains content that violates our usage policy.',
    blockedOutputsMessaging='The response was blocked due to content policy.'
)

print(f"Guardrail created: {response['guardrailId']}")