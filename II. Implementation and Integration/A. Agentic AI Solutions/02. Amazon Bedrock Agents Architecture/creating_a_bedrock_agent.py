import boto3

bedrock_agent = boto3.client('bedrock-agent')

# Step 1: Create the agent
agent_response = bedrock_agent.create_agent(
    agentName='travel-planning-agent',
    description='AI agent that helps plan travel itineraries',
    instruction="""You are a helpful travel planning assistant. You can:
    1. Search for flights between cities
    2. Find hotels based on preferences
    3. Create detailed itineraries
    4. Provide destination information

    Always confirm details before making bookings.
    Be concise but thorough in your recommendations.""",
    foundationModel='anthropic.claude-3-sonnet-20240229-v1:0',
    idleSessionTTLInSeconds00,  # 30 minutes
    agentResourceRoleArn='arn:aws:iam::123456789012:role/BedrockAgentRole'
)

agent_id = agent_response['agent']['agentId']
print(f"Created agent: {agent_id}")