import boto3

bedrock = boto3.client('bedrock')

response = bedrock.create_guardrail(
    name='pii-protection-guardrail',
    description='Comprehensive PII detection and protection',

    sensitiveInformationPolicyConfig={
        # Built-in PII entity detection
        'piiEntitiesConfig': [
            # Identity - Anonymize for personalization
            {'type': 'NAME', 'action': 'ANONYMIZE'},
            {'type': 'EMAIL', 'action': 'ANONYMIZE'},
            {'type': 'PHONE', 'action': 'ANONYMIZE'},
            {'type': 'ADDRESS', 'action': 'ANONYMIZE'},

            # Government IDs - Always block
            {'type': 'US_SOCIAL_SECURITY_NUMBER', 'action': 'BLOCK'},
            {'type': 'US_PASSPORT_NUMBER', 'action': 'BLOCK'},
            {'type': 'DRIVER_LICENSE', 'action': 'BLOCK'},

            # Financial - Always block
            {'type': 'CREDIT_DEBIT_CARD_NUMBER', 'action': 'BLOCK'},
            {'type': 'CREDIT_DEBIT_CARD_CVV', 'action': 'BLOCK'},
            {'type': 'BANK_ACCOUNT_NUMBER', 'action': 'BLOCK'},

            # Security credentials - Always block
            {'type': 'AWS_ACCESS_KEY', 'action': 'BLOCK'},
            {'type': 'AWS_SECRET_KEY', 'action': 'BLOCK'},
            {'type': 'PASSWORD', 'action': 'BLOCK'},

            # Technical identifiers - Anonymize
            {'type': 'IP_ADDRESS', 'action': 'ANONYMIZE'},
            {'type': 'USERNAME', 'action': 'ANONYMIZE'}
        ],

        # Custom regex patterns for domain-specific data
        'regexesConfig': [
            {
                'name': 'Employee ID',
                'description': 'Internal employee identifier',
                'pattern': r'EMP\d{6}',
                'action': 'ANONYMIZE'
            },
            {
                'name': 'Customer Account',
                'description': 'Customer account number format',
                'pattern': r'ACCT-[A-Z]{2}\d{8}',
                'action': 'ANONYMIZE'
            },
            {
                'name': 'Internal Project Code',
                'description': 'Confidential project identifiers',
                'pattern': r'PROJECT-[A-Z]{3}-\d{4}',
                'action': 'BLOCK'
            },
            {
                'name': 'API Key Pattern',
                'description': 'Custom API key format',
                'pattern': r'sk_live_[a-zA-Z0-9]{32}',
                'action': 'BLOCK'
            }
        ]
    },

    blockedInputMessaging='Your message contains sensitive information that cannot be processed.',
    blockedOutputsMessaging='The response contained sensitive information and was blocked.'
)

print(f"Guardrail created: {response['guardrailId']}")