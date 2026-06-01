import boto3
from datetime import datetime

bedrock_runtime = boto3.client('bedrock-agent-runtime')

def invoke_agent_with_memory(
    agent_id: str,
    agent_alias_id: str,
    user_id: str,
    user_message: str
):
    """Invoke agent with cross-session memory."""

    # Generate unique session ID for this conversation
    session_id = f"{user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Use consistent memoryId for the user (enables cross-session memory)
    memory_id = f"memory-{user_id}"

    response = bedrock_runtime.invoke_agent(
        agentId=agent_id,
        agentAliasId=agent_alias_id,
        sessionId=session_id,
        memoryId=memory_id,  # Critical for cross-session memory
        inputText=user_message
    )

    completion = ""
    for event in response['completion']:
        if 'chunk' in event:
            completion += event['chunk']['bytes'].decode('utf-8')

    return completion

# Day 1: First conversation
response = invoke_agent_with_memory(
    agent_id='AGENT123',
    agent_alias_id='ALIAS123',
    user_id='customer-456',
    user_message="I prefer window seats when booking flights"
)

# Day 7: New session - agent remembers preference
response = invoke_agent_with_memory(
    agent_id='AGENT123',
    agent_alias_id='ALIAS123',
    user_id='customer-456',
    user_message="Book me a flight to New York"
)
# Agent will proactively offer window seats based on remembered preference