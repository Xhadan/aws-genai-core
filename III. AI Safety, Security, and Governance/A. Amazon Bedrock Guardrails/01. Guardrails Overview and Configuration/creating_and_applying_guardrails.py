import boto3
import json

bedrock = boto3.client('bedrock')
bedrock_runtime = boto3.client('bedrock-runtime')

# Step 1: Create a guardrail
create_response = bedrock.create_guardrail(
    name='customer-support-guardrail',
    description='Guardrail for customer support chatbot',

    # Content filters
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

    # Denied topics
    topicPolicyConfig={
        'topicsConfig': [
            {
                'name': 'Competitor Products',
                'definition': 'Any discussion about competitor products or services',
                'examples': [
                    'What do you think about CompetitorX?',
                    'How does your product compare to CompetitorY?'
                ],
                'type': 'DENY'
            }
        ]
    },

    # Sensitive information filters
    sensitiveInformationPolicyConfig={
        'piiEntitiesConfig': [
            {'type': 'EMAIL', 'action': 'ANONYMIZE'},
            {'type': 'PHONE', 'action': 'ANONYMIZE'},
            {'type': 'US_SOCIAL_SECURITY_NUMBER', 'action': 'BLOCK'},
            {'type': 'CREDIT_DEBIT_CARD_NUMBER', 'action': 'BLOCK'}
        ]
    },

    # Blocked messaging
    blockedInputMessaging='I cannot process this request due to safety guidelines.',
    blockedOutputsMessaging='I cannot provide this response due to safety guidelines.'
)

guardrail_id = create_response['guardrailId']
guardrail_version = create_response['version']

print(f"Created guardrail: {guardrail_id} version {guardrail_version}")

# Step 2: Apply guardrail with model invocation
response = bedrock_runtime.converse(
    modelId='anthropic.claude-3-sonnet-20240229-v1:0',
    messages=[
        {'role': 'user', 'content': [{'text': 'How can I contact support?'}]}
    ],
    guardrailConfig={
        'guardrailIdentifier': guardrail_id,
        'guardrailVersion': guardrail_version
    }
)

# Check guardrail assessment
if 'trace' in response:
    guardrail_trace = response['trace'].get('guardrail', {})
    print(f"Guardrail action: {guardrail_trace.get('action')}")