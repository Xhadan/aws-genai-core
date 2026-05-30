response = bedrock_runtime.invoke_agent(
    agentId=agent_id,
    agentAliasId=agent_alias_id,
    sessionId=session_id,
    memoryId=f"memory-{user_id}",  # Required for persistence
    inputText=user_message
)