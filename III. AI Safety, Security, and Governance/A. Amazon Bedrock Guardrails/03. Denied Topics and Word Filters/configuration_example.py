import boto3

bedrock = boto3.client('bedrock')

response = bedrock.create_guardrail(
    name='business-policy-guardrail',
    description='Blocks competitor discussions and sensitive terms',

    # Denied Topics Configuration
    topicPolicyConfig={
        'topicsConfig': [
            {
                'name': 'Competitor Products',
                'definition': 'Any discussion comparing our products to competitors or recommending competitor products',
                'examples': [
                    'How does your product compare to CompetitorX?',
                    'Should I use CompetitorY instead?',
                    'What are the differences between you and CompetitorZ?',
                    'Is CompetitorX better for my use case?',
                    'Why should I choose you over the competition?'
                ],
                'type': 'DENY'
            },
            {
                'name': 'Investment Advice',
                'definition': 'Specific recommendations about buying, selling, or holding financial instruments',
                'examples': [
                    'Should I buy Apple stock?',
                    'What crypto should I invest in?',
                    'Is now a good time to sell my bonds?',
                    'Give me stock tips',
                    'Which ETFs do you recommend?'
                ],
                'type': 'DENY'
            },
            {
                'name': 'Medical Diagnosis',
                'definition': 'Diagnosing medical conditions or prescribing treatments',
                'examples': [
                    'Do I have cancer?',
                    'What medication should I take for this?',
                    'Diagnose my symptoms',
                    'What disease do I have?',
                    'Should I stop taking my medicine?'
                ],
                'type': 'DENY'
            }
        ]
    },

    # Word Filters Configuration
    wordPolicyConfig={
        # Enable managed profanity filter
        'managedWordListsConfig': [
            {'type': 'PROFANITY'}
        ],
        # Custom word list
        'wordsConfig': [
            {'text': 'CompetitorX'},
            {'text': 'CompetitorY'},
            {'text': 'CompetitorZ'},
            {'text': 'Project Phoenix'},
            {'text': 'Q4 roadmap'},
            {'text': 'unreleased feature'}
        ],
        # Regex patterns
        'regexesConfig': [
            {
                'name': 'Internal Ticket ID',
                'description': 'Block internal JIRA ticket references',
                'pattern': r'ACME-\d{3,6}',
                'action': 'BLOCK'
            },
            {
                'name': 'Internal Employee ID',
                'description': 'Block employee ID patterns',
                'pattern': r'EMP\d{6}',
                'action': 'BLOCK'
            }
        ]
    },

    blockedInputMessaging='I cannot discuss that topic.',
    blockedOutputsMessaging='I cannot provide that information.'
)

print(f"Guardrail created: {response['guardrailId']}")