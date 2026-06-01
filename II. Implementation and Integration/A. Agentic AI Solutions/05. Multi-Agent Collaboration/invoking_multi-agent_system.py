import boto3

bedrock_runtime = boto3.client('bedrock-agent-runtime')

def invoke_multi_agent(
    supervisor_id: str,
    supervisor_alias_id: str,
    session_id: str,
    user_message: str
):
    """Invoke the multi-agent system through the supervisor."""

    response = bedrock_runtime.invoke_agent(
        agentId=supervisor_id,
        agentAliasId=supervisor_alias_id,
        sessionId=session_id,
        inputText=user_message,
        enableTrace=True  # See which collaborators are invoked
    )

    result = {
        'completion': '',
        'collaborators_invoked': []
    }

    for event in response['completion']:
        if 'chunk' in event:
            result['completion'] += event['chunk']['bytes'].decode('utf-8')

        # Track collaborator invocations in trace
        if 'trace' in event:
            trace = event['trace'].get('trace', {})
            if 'orchestrationTrace' in trace:
                orch = trace['orchestrationTrace']
                if 'invocationInput' in orch:
                    inv = orch['invocationInput']
                    if 'collaboratorInvocationInput' in inv:
                        collab = inv['collaboratorInvocationInput']
                        result['collaborators_invoked'].append(collab.get('collaboratorName'))

    return result

# Example invocations
session_id = "user-123-multi-agent"

# Simple query - will be routed directly (in routing mode)
response1 = invoke_multi_agent(
    supervisor_id='SUPERVISOR123',
    supervisor_alias_id='ALIAS123',
    session_id=session_id,
    user_message="What's my current invoice balance?"
)
print(f"Response: {response1['completion']}")
print(f"Collaborators: {response1['collaborators_invoked']}")
# Expected: ['BillingSpecialist']

# Complex query - will use full orchestration
response2 = invoke_multi_agent(
    supervisor_id='SUPERVISOR123',
    supervisor_alias_id='ALIAS123',
    session_id=session_id,
    user_message="My app is crashing and I want to upgrade to fix it. Also check if I have any unpaid invoices."
)
print(f"Response: {response2['completion']}")
print(f"Collaborators: {response2['collaborators_invoked']}")
# Expected: ['TechnicalSupport', 'SalesSpecialist', 'BillingSpecialist']