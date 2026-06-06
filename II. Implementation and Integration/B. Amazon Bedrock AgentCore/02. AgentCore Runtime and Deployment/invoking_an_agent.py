import boto3
import json

agentcore = boto3.client('bedrock-agentcore')

# Invoke the agent synchronously
response = agentcore.invoke_agent(
    endpointName='enterprise-assistant',
    sessionId='user-12345-session-001',  # Session isolation
    inputText='Find information about our refund policy and notify the support team.',

    # Optional: Pass user context
    sessionAttributes={
        'userId': 'user-12345',
        'department': 'Sales',
        'accessLevel': 'standard'
    }
)

# Handle the response
result = json.loads(response['output'])
print(f"Agent response: {result['message']}")
print(f"Actions taken: {result['actions']}")

# Invoke with streaming for real-time responses
response_stream = agentcore.invoke_agent_with_stream(
    endpointName='enterprise-assistant',
    sessionId='user-12345-session-001',
    inputText='Explain the refund process step by step.'
)

for event in response_stream['responseStream']:
    if 'chunk' in event:
        print(event['chunk']['text'], end='')