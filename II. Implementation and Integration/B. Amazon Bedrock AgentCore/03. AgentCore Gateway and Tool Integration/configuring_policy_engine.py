import boto3

agentcore = boto3.client('bedrock-agentcore')

# Create a Policy Engine with Cedar policies
response = agentcore.create_policy_engine(
    policyEngineName='customer-service-policies',
    description='Policies for customer service agents',

    # Cedar policies as list of policy statements
    policies=[
        {
            'policyId': 'allow-read-operations',
            'statement': '''
                permit (
                    principal,
                    action = Action::"invoke_tool",
                    resource
                ) when {
                    resource.operation in ["read", "search", "get"]
                };
            '''
        },
        {
            'policyId': 'restrict-delete-operations',
            'statement': '''
                forbid (
                    principal,
                    action = Action::"invoke_tool",
                    resource
                ) when {
                    resource.operation = "delete"
                };
            '''
        },
        {
            'policyId': 'limit-refunds-by-role',
            'statement': '''
                forbid (
                    principal,
                    action = Action::"invoke_tool",
                    resource = Tool::"process_refund"
                ) when {
                    context.request.amount > 500 &&
                    principal.role != "supervisor"
                };
            '''
        },
        {
            'policyId': 'business-hours-only',
            'statement': '''
                permit (
                    principal,
                    action = Action::"invoke_tool",
                    resource = Tool::"create_zendesk_ticket"
                ) when {
                    context.time.hour >= 9 && context.time.hour <= 17 &&
                    context.time.dayOfWeek in [1, 2, 3, 4, 5]
                };
            '''
        }
    ]
)

policy_engine_id = response['policyEngineId']

# Associate policy engine with gateway
agentcore.associate_gateway_policy(
    gatewayId=gateway_id,
    policyEngineId=policy_engine_id,
    enforcementMode='ENFORCE'  # or 'LOG_ONLY' for testing
)

print(f"Policy engine {policy_engine_id} associated with gateway")