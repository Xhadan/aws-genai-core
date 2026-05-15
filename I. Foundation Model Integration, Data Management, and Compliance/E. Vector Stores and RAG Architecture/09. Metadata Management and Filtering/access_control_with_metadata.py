def filtered_rag_with_access_control(query, user_roles, knowledge_base_id):
    """
    RAG query filtered by user's access roles.
    """
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

    # Build access filter based on user roles
    role_filters = [
        {'equals': {'key': 'access_level', 'value': 'public'}}  # Always include public
    ]

    # Add role-specific access
    for role in user_roles:
        role_filters.append({
            'listContains': {
                'key': 'allowed_roles',
                'value': role
            }
        })

    response = bedrock_agent_runtime.retrieve_and_generate(
        input={'text': query},
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': knowledge_base_id,
                'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0',
                'retrievalConfiguration': {
                    'vectorSearchConfiguration': {
                        'filter': {
                            'orAll': role_filters
                        }
                    }
                }
            }
        }
    )

    return response

# Example: User with engineering role
result = filtered_rag_with_access_control(
    query="What are the deployment procedures?",
    user_roles=['engineering', 'developer'],
    knowledge_base_id='KB12345678'
)