import boto3

bedrock_agent = boto3.client('bedrock-agent')

def associate_guardrail_with_agent(
    agent_id: str,
    guardrail_id: str,
    guardrail_version: str
):
    """Associate a guardrail with an existing agent."""

    response = bedrock_agent.update_agent(
        agentId=agent_id,
        agentName='customer-service-agent',
        foundationModel='anthropic.claude-3-sonnet-20240229-v1:0',
        agentResourceRoleArn='arn:aws:iam::123456789012:role/BedrockAgentRole',
        instruction='You are a helpful customer service agent...',
        guardrailConfiguration={
            'guardrailIdentifier': guardrail_id,
            'guardrailVersion': guardrail_version
        }
    )

    # Prepare agent to apply changes
    bedrock_agent.prepare_agent(agentId=agent_id)

    return response


# Alternative: Create agent with guardrail from the start
def create_agent_with_guardrail(guardrail_id: str, guardrail_version: str):
    """Create a new agent with guardrail attached."""

    response = bedrock_agent.create_agent(
        agentName='secure-customer-agent',
        foundationModel='anthropic.claude-3-sonnet-20240229-v1:0',
        agentResourceRoleArn='arn:aws:iam::123456789012:role/BedrockAgentRole',
        instruction='''You are a secure customer service agent.
        Always follow safety guidelines and never disclose sensitive information.
        If asked to do something inappropriate, politely decline.''',
        guardrailConfiguration={
            'guardrailIdentifier': guardrail_id,
            'guardrailVersion': guardrail_version
        }
    )

    return response['agent']['agentId']