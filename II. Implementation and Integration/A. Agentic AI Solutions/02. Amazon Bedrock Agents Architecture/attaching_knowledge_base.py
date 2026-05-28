# Step 3: Associate knowledge base for destination info
kb_response = bedrock_agent.associate_agent_knowledge_base(
    agentId=agent_id,
    agentVersion='DRAFT',
    knowledgeBaseId='KB12345678',
    description='Travel destination guides and information',
    knowledgeBaseState='ENABLED'
)

# Step 4: Prepare the agent (required after changes)
bedrock_agent.prepare_agent(agentId=agent_id)

# Step 5: Create alias for deployment
alias_response = bedrock_agent.create_agent_alias(
    agentId=agent_id,
    agentAliasName='production',
    description='Production alias',
    routingConfiguration=[
        {
            'agentVersion': '1'  # Or specific version number
        }
    ]
)