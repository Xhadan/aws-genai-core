# Always set max iterations
agent = ReActAgent(max_iterations)

# Or with Bedrock Agents, use session timeout
response = bedrock_runtime.invoke_agent(
    # ... parameters
    idleSessionTTLInSeconds00  # 5 minute timeout
)