import boto3

bedrock = boto3.client('bedrock')

# Create guardrail with Automated Reasoning Checks
response = bedrock.create_guardrail(
    name='insurance-compliance-guardrail',
    description='Verifies insurance claim responses comply with policies',

    # Automated Reasoning Configuration
    automatedReasoningConfig={
        'policies': [
            {
                'name': 'auto-claim-requirements',
                'description': 'Required fields for auto insurance claims',
                'policy': '''
                    All auto insurance claim responses must include:
                    - Vehicle make and manufacturer
                    - Vehicle model name
                    - Vehicle year of manufacture
                    - Date of incident
                    - Description of damage

                    If the vehicle is more than 20 years old, the response
                    must also mention that classic vehicle documentation
                    is required.

                    If the claim amount exceeds $10,000, the response must
                    indicate that adjuster inspection is required.
                '''
            },
            {
                'name': 'claim-amount-validation',
                'description': 'Validates claim amount statements',
                'policy': '''
                    Any stated claim amount must be a positive number.
                    Claim amounts cannot exceed the policy coverage limit.
                    If partial payment is mentioned, it must be less than
                    or equal to the total claim amount.
                '''
            },
            {
                'name': 'timeline-consistency',
                'description': 'Ensures date logic is consistent',
                'policy': '''
                    The incident date must be before or on today's date.
                    The claim filing date must be on or after the incident date.
                    Any estimated repair completion date must be after
                    the incident date.
                '''
            }
        ]
    },

    blockedInputMessaging='Unable to process this request.',
    blockedOutputsMessaging='The response did not meet compliance requirements.'
)

print(f"Guardrail created: {response['guardrailId']}")