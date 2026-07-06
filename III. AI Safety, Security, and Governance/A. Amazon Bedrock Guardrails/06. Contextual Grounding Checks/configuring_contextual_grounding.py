import boto3

bedrock = boto3.client('bedrock')

# Create guardrail with contextual grounding
response = bedrock.create_guardrail(
    name='rag-grounding-guardrail',
    description='Ensures RAG responses are grounded and relevant',

    # Contextual Grounding Configuration
    contextualGroundingPolicyConfig={
        'filtersConfig': [
            {
                'type': 'GROUNDING',
                'threshold': 0.75  # Require 75% grounding score
            },
            {
                'type': 'RELEVANCE',
                'threshold': 0.65  # Require 65% relevance score
            }
        ]
    },

    # Also include content filters for safety
    contentPolicyConfig={
        'filtersConfig': [
            {'type': 'HATE', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
            {'type': 'INSULTS', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
            {'type': 'SEXUAL', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
            {'type': 'VIOLENCE', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
            {'type': 'MISCONDUCT', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
            {'type': 'PROMPT_ATTACK', 'inputStrength': 'HIGH', 'outputStrength': 'NONE'}
        ]
    },

    blockedInputMessaging='Unable to process this request.',
    blockedOutputsMessaging='The response could not be verified against source material.'
)

print(f"Guardrail created: {response['guardrailId']}")