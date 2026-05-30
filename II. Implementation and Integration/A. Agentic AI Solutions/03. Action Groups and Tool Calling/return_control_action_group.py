# Create action group that returns control to client
response = bedrock_agent.create_agent_action_group(
    agentId='AGENT123',
    agentVersion='DRAFT',
    actionGroupName='user-confirmations',
    description='Actions requiring user confirmation before execution',
    actionGroupExecutor={
        'customControl': 'RETURN_CONTROL'  # Return to client
    },
    apiSchema={
        'payload': '''
openapi: 3.0.0
info:
  title: Confirmation API
  version: 1.0.0
paths:
  /confirm-purchase:
    post:
      operationId: confirmPurchase
      description: Request user confirmation for a purchase over $100
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                amount:
                  type: number
                items:
                  type: array
      responses:
        "200":
          description: Confirmation status
'''
    }
)

# Client-side handling of Return Control
def handle_agent_response(response):
    """Handle agent response including Return Control."""
    for event in response['completion']:
        if 'returnControl' in event:
            # Agent wants client to handle this action
            invocation = event['returnControl']['invocationInputs'][0]
            action = invocation['apiInvocationInput']

            print(f"Agent requests: {action['actionGroup']}/{action['apiPath']}")
            print(f"Parameters: {action['requestBody']}")

            # Execute client-side (e.g., show confirmation dialog)
            user_confirmed = show_confirmation_dialog(action)

            # Send result back to agent
            return continue_agent_session(
                session_id=response['sessionId'],
                action_result=user_confirmed
            )