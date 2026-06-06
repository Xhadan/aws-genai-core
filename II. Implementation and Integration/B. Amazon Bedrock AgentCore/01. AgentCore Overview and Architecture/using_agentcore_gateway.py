import boto3

agentcore = boto3.client('bedrock-agentcore')

# Create Gateway endpoint with tools
response = agentcore.create_gateway(
    gatewayName='enterprise-tools-gateway',
    description='Gateway for enterprise tool access',

    # Define tools from various sources
    tools=[
        {
            'name': 'search_customers',
            'type': 'LAMBDA',
            'lambdaArn': 'arn:aws:lambda:us-east-1:123456789012:function:SearchCustomers',
            'description': 'Search customer database'
        },
        {
            'name': 'create_ticket',
            'type': 'API',
            'apiEndpoint': 'https://api.zendesk.com/tickets',
            'authType': 'OAUTH',
            'oauthConfig': {
                'clientId': '{{secretsmanager:zendesk-oauth}}',
                'scopes': ['tickets:write']
            }
        },
        {
            'name': 'slack_message',
            'type': 'MCP_SERVER',
            'mcpServerUri': 'mcp://slack-mcp-server.example.com'
        }
    ],

    # Associate policy for access control
    policyEngineId='policy-engine-id'
)

gateway_id = response['gatewayId']
gateway_endpoint = response['endpoint']