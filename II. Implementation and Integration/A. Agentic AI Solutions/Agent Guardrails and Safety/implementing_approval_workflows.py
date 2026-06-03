import boto3

bedrock_agent = boto3.client('bedrock-agent')
bedrock_runtime = boto3.client('bedrock-agent-runtime')

# Create action group requiring approval for sensitive actions
def create_approval_action_group(agent_id: str):
    """Create action group that returns control for approval."""

    api_schema = '''
openapi: 3.0.0
info:
  title: Sensitive Actions API
  version: 1.0.0
paths:
  /delete-data:
    post:
      operationId: deleteUserData
      description: |
        Permanently delete user data. This action is IRREVERSIBLE.
        Only use when user explicitly requests data deletion.
        REQUIRES USER CONFIRMATION before execution.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - userId
                - dataTypes
              properties:
                userId:
                  type: string
                dataTypes:
                  type: array
                  items:
                    type: string
                    enum: [orders, profile, preferences, all]
      responses:
        "200":
          description: Deletion confirmation
  /refund-order:
    post:
      operationId: processRefund
      description: |
        Process a refund for an order. Amounts over $100 require supervisor approval.
        Verify order eligibility before processing.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - orderId
                - amount
                - reason
              properties:
                orderId:
                  type: string
                amount:
                  type: number
                reason:
                  type: string
      responses:
        "200":
          description: Refund status
'''

    response = bedrock_agent.create_agent_action_group(
        agentId=agent_id,
        agentVersion='DRAFT',
        actionGroupName='sensitive-actions',
        description='Actions requiring user confirmation',
        actionGroupExecutor={
            'customControl': 'RETURN_CONTROL'  # Returns to client for approval
        },
        apiSchema={
            'payload': api_schema
        }
    )

    return response


def handle_agent_with_approval(agent_id: str, alias_id: str, session_id: str, query: str):
    """Handle agent responses including approval workflow."""

    response = bedrock_runtime.invoke_agent(
        agentId=agent_id,
        agentAliasId=alias_id,
        sessionId=session_id,
        inputText=query
    )

    for event in response['completion']:
        if 'chunk' in event:
            print(event['chunk']['bytes'].decode('utf-8'), end='')

        # Handle Return Control for approval
        if 'returnControl' in event:
            invocation = event['returnControl']['invocationInputs'][0]
            api_input = invocation.get('apiInvocationInput', {})

            action_name = api_input.get('apiPath', 'unknown')
            parameters = api_input.get('requestBody', {})

            print(f"\n\n== APPROVAL REQUIRED ==")
            print(f"Action: {action_name}")
            print(f"Parameters: {parameters}")

            # In production, this would be a proper approval UI
            approval = input("\nApprove this action? (yes/no): ")

            if approval.lower() = 'yes':
                # Continue agent with approval
                result = execute_approved_action(api_input)
                return continue_session_with_result(
                    agent_id, alias_id, session_id,
                    event['returnControl']['invocationId'],
                    result
                )
            else:
                # Continue with rejection
                return continue_session_with_result(
                    agent_id, alias_id, session_id,
                    event['returnControl']['invocationId'],
                    {'status': 'rejected', 'message': 'User declined the action'}
                )


def continue_session_with_result(agent_id, alias_id, session_id, invocation_id, result):
    """Continue agent session with action result."""
    import json

    response = bedrock_runtime.invoke_agent(
        agentId=agent_id,
        agentAliasId=alias_id,
        sessionId=session_id,
        sessionState={
            'returnControlInvocationResults': [
                {
                    'invocationId': invocation_id,
                    'apiResult': {
                        'actionGroup': 'sensitive-actions',
                        'httpStatusCode': 200,
                        'responseBody': {
                            'application/json': {
                                'body': json.dumps(result)
                            }
                        }
                    }
                }
            ]
        }
    )

    # Process response
    completion = ""
    for event in response['completion']:
        if 'chunk' in event:
            completion += event['chunk']['bytes'].decode('utf-8')

    return completion