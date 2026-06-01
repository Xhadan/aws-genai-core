import boto3
import json

bedrock_runtime = boto3.client('bedrock-agent-runtime')

def invoke_agent_with_session_state(
    agent_id: str,
    agent_alias_id: str,
    session_id: str,
    user_message: str,
    session_attributes: dict = None,
    prompt_attributes: dict = None
):
    """Invoke agent with session state management."""

    # Build session state
    session_state = {}

    if session_attributes:
        session_state['sessionAttributes'] = session_attributes

    if prompt_attributes:
        session_state['promptSessionAttributes'] = prompt_attributes

    # Invoke agent
    response = bedrock_runtime.invoke_agent(
        agentId=agent_id,
        agentAliasId=agent_alias_id,
        sessionId=session_id,
        inputText=user_message,
        sessionState=session_state if session_state else None
    )

    # Process streaming response
    completion = ""
    for event in response['completion']:
        if 'chunk' in event:
            completion += event['chunk']['bytes'].decode('utf-8')

    return completion

# Example: E-commerce conversation with session state
session_id = "user-123-session-456"

# Turn 1: User browses products
response1 = invoke_agent_with_session_state(
    agent_id='AGENT123',
    agent_alias_id='ALIAS123',
    session_id=session_id,
    user_message="Show me running shoes under $100",
    session_attributes={
        'userId': 'USER-123',
        'cartItems': '[]',
        'browsingCategory': 'footwear'
    }
)

# Turn 2: Continue conversation - agent remembers context
response2 = invoke_agent_with_session_state(
    agent_id='AGENT123',
    agent_alias_id='ALIAS123',
    session_id=session_id,
    user_message="Add the second one to my cart",  # Agent knows "second" from context
    session_attributes={
        'userId': 'USER-123',
        'cartItems': json.dumps([{'product': 'RunPro-X', 'price': 89.99}]),
        'browsingCategory': 'footwear'
    }
)