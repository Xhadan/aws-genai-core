import boto3
import json

# Step Functions state machine definition for custom orchestration
state_machine_definition = {
    "Comment": "Custom agent orchestration with explicit control flow",
    "StartAt": "ClassifyIntent",
    "States": {
        "ClassifyIntent": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:classify-intent",
            "ResultPath": "$.classification",
            "Next": "RouteByIntent"
        },
        "RouteByIntent": {
            "Type": "Choice",
            "Choices": [
                {
                    "Variable": "$.classification.intent",
                    "StringEquals": "order_status",
                    "Next": "LookupOrder"
                },
                {
                    "Variable": "$.classification.intent",
                    "StringEquals": "product_search",
                    "Next": "SearchProducts"
                },
                {
                    "Variable": "$.classification.intent",
                    "StringEquals": "complex_query",
                    "Next": "ReActLoop"
                }
            ],
            "Default": "GenerateResponse"
        },
        "LookupOrder": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:lookup-order",
            "ResultPath": "$.order_data",
            "Next": "GenerateResponse"
        },
        "SearchProducts": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:search-products",
            "ResultPath": "$.product_data",
            "Next": "GenerateResponse"
        },
        "ReActLoop": {
            "Type": "Task",
            "Resource": "arn:aws:states:::bedrock:invokeAgent",
            "Parameters": {
                "AgentId": "AGENT123",
                "AgentAliasId": "ALIAS123",
                "SessionId.$": "$.session_id",
                "InputText.$": "$.query"
            },
            "ResultPath": "$.agent_response",
            "Next": "CheckCompletion"
        },
        "CheckCompletion": {
            "Type": "Choice",
            "Choices": [
                {
                    "Variable": "$.agent_response.requires_approval",
                    "BooleanEquals": True,
                    "Next": "RequestApproval"
                }
            ],
            "Default": "GenerateResponse"
        },
        "RequestApproval": {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
            "Parameters": {
                "FunctionName": "request-human-approval",
                "Payload": {
                    "action.$": "$.agent_response.pending_action",
                    "taskToken.$": "$$.Task.Token"
                }
            },
            "ResultPath": "$.approval",
            "Next": "ExecuteApprovedAction"
        },
        "ExecuteApprovedAction": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:execute-action",
            "ResultPath": "$.action_result",
            "Next": "GenerateResponse"
        },
        "GenerateResponse": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:generate-response",
            "End": True
        }
    }
}

# Create Step Functions state machine
sfn = boto3.client('stepfunctions')

def create_orchestration_workflow():
    """Create custom orchestration state machine."""
    response = sfn.create_state_machine(
        name='agent-custom-orchestration',
        definition=json.dumps(state_machine_definition),
        roleArn='arn:aws:iam::123456789012:role/StepFunctionsAgentRole',
        type='STANDARD'
    )
    return response['stateMachineArn']

def invoke_orchestrated_agent(state_machine_arn: str, query: str, session_id: str):
    """Start custom orchestration execution."""
    response = sfn.start_execution(
        stateMachineArn=state_machine_arn,
        input=json.dumps({
            'query': query,
            'session_id': session_id
        })
    )
    return response['executionArn']