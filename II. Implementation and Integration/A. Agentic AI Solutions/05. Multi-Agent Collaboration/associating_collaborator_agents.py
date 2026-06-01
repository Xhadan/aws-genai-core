import boto3

bedrock_agent = boto3.client('bedrock-agent')

def prepare_agent(agent_id: str):
    """Prepare agent for deployment."""
    response = bedrock_agent.prepare_agent(agentId=agent_id)
    return response

def associate_collaborator(
    supervisor_id: str,
    collaborator_id: str,
    collaborator_name: str,
    relationship_instruction: str
):
    """Associate a collaborator agent with the supervisor."""

    # First, prepare the collaborator agent
    prepare_agent(collaborator_id)

    # Associate with supervisor
    response = bedrock_agent.associate_agent_collaborator(
        agentId=supervisor_id,
        agentVersion='DRAFT',
        agentDescriptor={
            'aliasArn': f'arn:aws:bedrock:us-east-1:123456789012:agent-alias/{collaborator_id}/TSTALIASID'
        },
        collaboratorName=collaborator_name,
        collaborationInstruction=relationship_instruction,
        relayConversationHistory='TO_COLLABORATOR'  # Share conversation context
    )

    return response

# Associate all collaborators
associate_collaborator(
    supervisor_id=supervisor_id,
    collaborator_id=billing_agent_id,
    collaborator_name='BillingSpecialist',
    relationship_instruction='''Route billing, payment, invoice, and subscription
    questions to this agent. Include relevant account context.'''
)

associate_collaborator(
    supervisor_id=supervisor_id,
    collaborator_id=technical_agent_id,
    collaborator_name='TechnicalSupport',
    relationship_instruction='''Route technical issues, troubleshooting, configuration,
    and error-related questions to this agent. Include error messages and symptoms.'''
)

associate_collaborator(
    supervisor_id=supervisor_id,
    collaborator_id=sales_agent_id,
    collaborator_name='SalesSpecialist',
    relationship_instruction='''Route product inquiries, pricing questions, upgrade
    requests, and feature questions to this agent.'''
)

# Prepare supervisor with collaborators
prepare_agent(supervisor_id)
print("Multi-agent system configured successfully")