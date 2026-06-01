import boto3

bedrock_agent = boto3.client('bedrock-agent')

def list_memory_sessions(agent_id: str, agent_alias_id: str, memory_id: str):
    """List all memory sessions for a user."""

    response = bedrock_agent.list_agent_memory(
        agentId=agent_id,
        agentAliasId=agent_alias_id,
        memoryId=memory_id,
        memoryType='SESSION_SUMMARY'
    )

    sessions = []
    for memory_content in response.get('memoryContents', []):
        if 'sessionSummary' in memory_content:
            summary = memory_content['sessionSummary']
            sessions.append({
                'sessionId': summary.get('sessionId'),
                'startTime': summary.get('sessionStartTime'),
                'expiryTime': summary.get('sessionExpiryTime'),
                'summary': summary.get('summaryText')
            })

    return sessions

def delete_memory(agent_id: str, agent_alias_id: str, memory_id: str):
    """Delete all memory for a user (GDPR compliance)."""

    response = bedrock_agent.delete_agent_memory(
        agentId=agent_id,
        agentAliasId=agent_alias_id,
        memoryId=memory_id
    )

    return response

# Example usage
sessions = list_memory_sessions('AGENT123', 'ALIAS123', 'memory-customer-456')
for session in sessions:
    print(f"Session: {session['sessionId']}")
    print(f"Summary: {session['summary']}")
    print("---")