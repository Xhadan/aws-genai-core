import boto3

agentcore = boto3.client('bedrock-agentcore')

# Create a Gateway with multiple tool sources
response = agentcore.create_gateway(
    gatewayName='enterprise-tools-gateway',
    description='Unified tool access for enterprise agents',

    # Define tools from various sources
    toolConfigurations=[
        # Lambda function as tool
        {
            'toolName': 'search_customers',
            'toolType': 'LAMBDA',
            'lambdaConfig': {
                'functionArn': 'arn:aws:lambda:us-east-1:123456789012:function:SearchCustomers',
                'invocationType': 'RequestResponse'
            },
            'description': 'Search customer database by name, email, or account ID',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string', 'description': 'Search query'},
                    'searchType': {'type': 'string', 'enum': ['name', 'email', 'account_id']}
                },
                'required': ['query']
            }
        },

        # REST API as tool
        {
            'toolName': 'get_weather',
            'toolType': 'HTTP',
            'httpConfig': {
                'endpoint': 'https://api.weather.com/v1/current',
                'method': 'GET',
                'headers': {
                    'X-API-Key': '{{secretsmanager:weather-api-key}}'
                }
            },
            'description': 'Get current weather for a location',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'city': {'type': 'string'},
                    'country': {'type': 'string'}
                },
                'required': ['city']
            }
        },

        # SaaS connector
        {
            'toolName': 'create_zendesk_ticket',
            'toolType': 'SAAS_CONNECTOR',
            'saasConfig': {
                'provider': 'ZENDESK',
                'operation': 'CREATE_TICKET',
                'authConfig': {
                    'type': 'OAUTH2',
                    'credentialsSecretArn': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:zendesk-oauth'
                }
            },
            'description': 'Create a support ticket in Zendesk'
        },

        # Existing MCP server
        {
            'toolName': 'slack_operations',
            'toolType': 'MCP_SERVER',
            'mcpConfig': {
                'serverUri': 'mcp://slack-mcp-server.internal:8080',
                'transportType': 'HTTP'
            },
            'description': 'Slack messaging and channel operations'
        }
    ],

    # VPC configuration for private backends
    vpcConfig={
        'subnetIds': ['subnet-123', 'subnet-456'],
        'securityGroupIds': ['sg-789']
    },

    tags=[
        {'Key': 'Environment', 'Value': 'Production'},
        {'Key': 'Team', 'Value': 'AI-Platform'}
    ]
)

gateway_id = response['gatewayId']
gateway_endpoint = response['gatewayEndpoint']
print(f"Gateway created: {gateway_id}")
print(f"Endpoint: {gateway_endpoint}")