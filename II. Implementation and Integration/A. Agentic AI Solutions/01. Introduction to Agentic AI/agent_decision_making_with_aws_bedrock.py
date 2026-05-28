import boto3

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

def invoke_agent(agent_id: str, agent_alias_id: str, session_id: str, prompt: str):
    """Invoke a Bedrock Agent with a user prompt."""

    response = bedrock_agent_runtime.invoke_agent(
        agentId=agent_id,
        agentAliasId=agent_alias_id,
        sessionId=session_id,
        inputText=prompt,
        enableTrace=True  # Enable reasoning trace
    )

    # Process streaming response
    completion = ""
    traces = []

    for event in response['completion']:
        if 'chunk' in event:
            completion += event['chunk']['bytes'].decode()
        if 'trace' in event:
            traces.append(event['trace'])

    return {
        'response': completion,
        'reasoning_traces': traces
    }

# Example: Invoke travel planning agent
result = invoke_agent(
    agent_id='AGENT123',
    agent_alias_id='TSTALIASID',
    session_id='user-session-456',
    prompt="Plan a 3-day trip to Seattle including flights and hotels"
)

print(f"Agent Response: {result['response']}")
# Agent breaks down task, searches flights, finds hotels, creates itinerary