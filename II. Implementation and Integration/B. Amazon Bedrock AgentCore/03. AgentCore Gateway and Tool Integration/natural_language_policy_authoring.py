import boto3

agentcore = boto3.client('bedrock-agentcore')

# Create policy using natural language description
response = agentcore.create_policy_from_natural_language(
    policyEngineName='customer-service-policies',

    # Natural language descriptions
    naturalLanguagePolicies=[
        {
            'description': 'Allow agents to search and read customer information',
            'intent': 'PERMIT'
        },
        {
            'description': 'Prevent agents from deleting any customer records',
            'intent': 'FORBID'
        },
        {
            'description': 'Only supervisors can process refunds over $500',
            'intent': 'FORBID'
        },
        {
            'description': 'Restrict ticket creation to business hours Monday through Friday',
            'intent': 'PERMIT'
        }
    ],

    # Tool schemas for context
    toolSchemas=[
        {
            'toolName': 'search_customers',
            'schema': {
                'operation': 'read',
                'parameters': ['query', 'searchType']
            }
        },
        {
            'toolName': 'process_refund',
            'schema': {
                'operation': 'write',
                'parameters': ['orderId', 'amount', 'reason']
            }
        }
    ]
)

# Review generated Cedar policies
for policy in response['generatedPolicies']:
    print(f"Generated policy: {policy['policyId']}")
    print(f"Cedar: {policy['cedarStatement']}")
    print(f"Validation: {policy['validationResult']}")
    print("---")

# Automated reasoning checks for:
# - Overly permissive policies
# - Overly restrictive policies
# - Conditions that can never be satisfied
# - Policy conflicts