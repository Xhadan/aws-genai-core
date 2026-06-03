import boto3

bedrock = boto3.client('bedrock')

def create_agent_guardrail():
    """Create a guardrail configuration for agents."""

    response = bedrock.create_guardrail(
        name='customer-service-agent-guardrail',
        description='Guardrails for customer service agent with tool access',

        # Block generation of harmful content
        contentPolicyConfig={
            'filtersConfig': [
                {
                    'type': 'HATE',
                    'inputStrength': 'HIGH',
                    'outputStrength': 'HIGH'
                },
                {
                    'type': 'INSULTS',
                    'inputStrength': 'MEDIUM',
                    'outputStrength': 'HIGH'
                },
                {
                    'type': 'SEXUAL',
                    'inputStrength': 'HIGH',
                    'outputStrength': 'HIGH'
                },
                {
                    'type': 'VIOLENCE',
                    'inputStrength': 'HIGH',
                    'outputStrength': 'HIGH'
                },
                {
                    'type': 'MISCONDUCT',
                    'inputStrength': 'HIGH',
                    'outputStrength': 'HIGH'
                },
                {
                    'type': 'PROMPT_ATTACK',
                    'inputStrength': 'HIGH',
                    'outputStrength': 'NONE'  # Only filter input
                }
            ]
        },

        # Define topics the agent should not discuss
        topicPolicyConfig={
            'topicsConfig': [
                {
                    'name': 'competitor-discussion',
                    'definition': 'Discussions comparing our products negatively to competitors or recommending competitor products',
                    'examples': [
                        'You should use CompetitorX instead',
                        'Our product is worse than CompetitorY'
                    ],
                    'type': 'DENY'
                },
                {
                    'name': 'financial-advice',
                    'definition': 'Specific investment or financial advice that could be considered professional financial guidance',
                    'examples': [
                        'You should invest in stocks',
                        'Buy cryptocurrency now'
                    ],
                    'type': 'DENY'
                },
                {
                    'name': 'medical-advice',
                    'definition': 'Medical diagnoses or treatment recommendations',
                    'examples': [
                        'You probably have condition X',
                        'Take this medication'
                    ],
                    'type': 'DENY'
                }
            ]
        },

        # Block specific words/phrases
        wordPolicyConfig={
            'wordsConfig': [
                {'text': 'confidential-internal-code'},
                {'text': 'admin-bypass'}
            ],
            'managedWordListsConfig': [
                {'type': 'PROFANITY'}
            ]
        },

        # Protect sensitive information
        sensitiveInformationPolicyConfig={
            'piiEntitiesConfig': [
                {'type': 'EMAIL', 'action': 'ANONYMIZE'},
                {'type': 'PHONE', 'action': 'ANONYMIZE'},
                {'type': 'US_SOCIAL_SECURITY_NUMBER', 'action': 'BLOCK'},
                {'type': 'CREDIT_DEBIT_CARD_NUMBER', 'action': 'BLOCK'},
                {'type': 'AWS_ACCESS_KEY', 'action': 'BLOCK'},
                {'type': 'AWS_SECRET_KEY', 'action': 'BLOCK'}
            ],
            'regexesConfig': [
                {
                    'name': 'internal-account-id',
                    'description': 'Internal account ID format',
                    'pattern': 'ACCT-[A-Z0-9]{10}',
                    'action': 'ANONYMIZE'
                },
                {
                    'name': 'api-key-pattern',
                    'description': 'API key format',
                    'pattern': 'sk-[a-zA-Z0-9]{32}',
                    'action': 'BLOCK'
                }
            ]
        },

        # Verify response grounding
        contextualGroundingPolicyConfig={
            'filtersConfig': [
                {
                    'type': 'GROUNDING',
                    'threshold': 0.7  # Require 70% grounding
                },
                {
                    'type': 'RELEVANCE',
                    'threshold': 0.6  # Require 60% relevance
                }
            ]
        },

        # Blocked input/output messages
        blockedInputMessaging='I cannot process this request as it violates our safety policies.',
        blockedOutputsMessaging='I cannot provide this response as it violates our safety policies.',

        tags=[
            {'key': 'Environment', 'value': 'Production'},
            {'key': 'Team', 'value': 'CustomerService'}
        ]
    )

    guardrail_id = response['guardrailId']
    print(f"Created guardrail: {guardrail_id}")

    # Create a version for production use
    version_response = bedrock.create_guardrail_version(
        guardrailIdentifier=guardrail_id,
        description='Initial production version'
    )

    return guardrail_id, version_response['version']


guardrail_id, version = create_agent_guardrail()