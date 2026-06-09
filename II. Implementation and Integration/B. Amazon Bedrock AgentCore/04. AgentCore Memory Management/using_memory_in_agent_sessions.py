import boto3
import json

agentcore = boto3.client('bedrock-agentcore')

# Start a session with memory enabled
session_response = agentcore.create_agent_session(
    endpointName='customer-support-agent',
    sessionId='session-abc123',
    userId='user-12345',  # Required for cross-session memory

    # Memory configuration
    memoryConfig={
        'memoryStoreId': 'customer-service-memory',
        'enableShortTermMemory': True,
        'enableLongTermMemory': True
    }
)

# Invoke agent - memory is automatically used
response = agentcore.invoke_agent(
    endpointName='customer-support-agent',
    sessionId='session-abc123',
    inputText='What was my last order?'
)

# Agent automatically retrieves relevant memories:
# - Previous conversation context (short-term)
# - Past order information (semantic long-term)
# - User preferences (long-term preferences)

print(f"Response: {response['output']}")

# View memory retrieval details
if 'memoryContext' in response:
    print(f"Retrieved memories: {response['memoryContext']['retrievedCount']}")
    for memory in response['memoryContext']['memories']:
        print(f"  - {memory['type']}: {memory['content']}")