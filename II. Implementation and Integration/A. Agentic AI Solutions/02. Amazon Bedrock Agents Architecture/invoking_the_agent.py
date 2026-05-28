import boto3

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

def invoke_agent_streaming(agent_id, alias_id, session_id, user_input):
    """Invoke agent with streaming response and tracing."""

    response = bedrock_agent_runtime.invoke_agent(
        agentId=agent_id,
        agentAliasId=alias_id,
        sessionId=session_id,
        inputText=user_input,
        enableTrace=True,
        sessionState={
            'sessionAttributes': {
                'userPreference': 'economy',
                'currency': 'USD'
            }
        }
    )

    # Process streaming response
    full_response = ""
    traces = []

    for event in response['completion']:
        # Handle response chunks
        if 'chunk' in event:
            chunk_text = event['chunk']['bytes'].decode('utf-8')
            full_response += chunk_text
            print(chunk_text, end='', flush=True)

        # Handle trace events (reasoning steps)
        if 'trace' in event:
            trace = event['trace']['trace']
            if 'orchestrationTrace' in trace:
                orch = trace['orchestrationTrace']
                if 'modelInvocationInput' in orch:
                    traces.append(('reasoning', orch['modelInvocationInput']))
                if 'invocationInput' in orch:
                    traces.append(('action', orch['invocationInput']))

    return {
        'response': full_response,
        'traces': traces
    }

# Usage
result = invoke_agent_streaming(
    agent_id='AGENT123',
    alias_id='production',
    session_id='user-session-001',
    user_input='Find flights from NYC to Seattle next Friday'
)