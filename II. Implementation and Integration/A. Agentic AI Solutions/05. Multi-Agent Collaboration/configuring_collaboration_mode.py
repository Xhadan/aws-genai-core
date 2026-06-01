import boto3

bedrock_agent = boto3.client('bedrock-agent')

def configure_collaboration_mode(agent_id: str, use_routing: bool = True):
    """Configure the collaboration mode for a supervisor agent."""

    # Update agent with collaboration settings
    response = bedrock_agent.update_agent(
        agentId=agent_id,
        agentName='customer-service-supervisor',
        foundationModel='anthropic.claude-3-sonnet-20240229-v1:0',
        agentResourceRoleArn='arn:aws:iam::123456789012:role/BedrockAgentRole',
        instruction='...',  # Your instruction
        agentCollaboration='SUPERVISOR_ROUTER' if use_routing else 'SUPERVISOR'
    )

    return response

# Enable supervisor with routing mode for better performance
configure_collaboration_mode(supervisor_id, use_routing=True)