import boto3
import json

agentcore = boto3.client('bedrock-agentcore')

# Invoke a tool through the gateway
response = agentcore.invoke_gateway_tool(
    gatewayId='gateway-12345',
    toolName='search_customers',
    sessionId='session-abc123',

    # Tool input parameters
    input={
        'query': 'john.doe@example.com',
        'searchType': 'email'
    },

    # Context for policy evaluation
    context={
        'userId': 'agent-user-001',
        'role': 'customer_service_rep',
        'department': 'support'
    }
)

# Check if tool execution was permitted
if response['policyDecision'] = 'PERMIT':
    result = json.loads(response['output'])
    print(f"Customer found: {result}")
else:
    print(f"Tool call denied: {response['policyReason']}")
    # Policy denial reason provided for debugging

# List available tools for an agent
tools = agentcore.list_gateway_tools(
    gatewayId='gateway-12345',
    sessionContext={
        'userId': 'agent-user-001',
        'role': 'customer_service_rep'
    }
)

# Returns only tools the agent is permitted to use
for tool in tools['tools']:
    print(f"Tool: {tool['name']} - {tool['description']}")