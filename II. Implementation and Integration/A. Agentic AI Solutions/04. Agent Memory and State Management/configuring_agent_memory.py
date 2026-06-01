import boto3

bedrock_agent = boto3.client('bedrock-agent')

# Create agent with memory configuration
response = bedrock_agent.create_agent(
    agentName='customer-support-agent',
    foundationModel='anthropic.claude-3-sonnet-20240229-v1:0',
    agentResourceRoleArn='arn:aws:iam::123456789012:role/BedrockAgentRole',
    instruction='You are a helpful customer support agent. Use memory to personalize responses.',
    memoryConfiguration={
        'enabledMemoryTypes': ['SESSION_SUMMARY'],
        'storageDays': 30,  # Retain memory for 30 days
        'sessionSummaryConfiguration': {
            'maxRecentSessions': 5  # Include last 5 sessions in context
        }
    }
)

agent_id = response['agent']['agentId']
print(f"Created agent with memory: {agent_id}")