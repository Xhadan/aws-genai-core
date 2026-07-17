import boto3
import json

stepfunctions = boto3.client('stepfunctions')
sns = boto3.client('sns')

def create_approval_workflow():
    """
    Create Step Functions state machine for human approval workflow.
    """
    # State machine definition
    definition = {
        "Comment": "Human-in-the-Loop Approval Workflow for GenAI",
        "StartAt": "GenerateContent",
        "States": {
            "GenerateContent": {
                "Type": "Task",
                "Resource": "arn:aws:lambda:us-east-1:123456789012:function:generate-content",
                "ResultPath": "$.aiOutput",
                "Next": "CheckConfidence"
            },
            "CheckConfidence": {
                "Type": "Choice",
                "Choices": [
                    {
                        "Variable": "$.aiOutput.confidence",
                        "NumericGreaterThanEquals": 0.9,
                        "Next": "AutoApprove"
                    },
                    {
                        "Variable": "$.aiOutput.confidence",
                        "NumericLessThan": 0.5,
                        "Next": "MandatoryReview"
                    }
                ],
                "Default": "OptionalReview"
            },
            "AutoApprove": {
                "Type": "Pass",
                "Result": {"approved": True, "method": "auto"},
                "ResultPath": "$.approval",
                "Next": "PublishContent"
            },
            "OptionalReview": {
                "Type": "Task",
                "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
                "Parameters": {
                    "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/review-queue",
                    "MessageBody": {
                        "taskToken.$": "$$.Task.Token",
                        "content.$": "$.aiOutput.content",
                        "confidence.$": "$.aiOutput.confidence",
                        "reviewType": "optional"
                    }
                },
                "TimeoutSeconds": 3600,
                "Catch": [
                    {
                        "ErrorEquals": ["States.Timeout"],
                        "ResultPath": "$.error",
                        "Next": "AutoApprove"
                    }
                ],
                "ResultPath": "$.approval",
                "Next": "CheckApproval"
            },
            "MandatoryReview": {
                "Type": "Task",
                "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
                "Parameters": {
                    "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/review-queue",
                    "MessageBody": {
                        "taskToken.$": "$$.Task.Token",
                        "content.$": "$.aiOutput.content",
                        "confidence.$": "$.aiOutput.confidence",
                        "reviewType": "mandatory"
                    }
                },
                "TimeoutSeconds": 86400,
                "ResultPath": "$.approval",
                "Next": "CheckApproval"
            },
            "CheckApproval": {
                "Type": "Choice",
                "Choices": [
                    {
                        "Variable": "$.approval.approved",
                        "BooleanEquals": True,
                        "Next": "PublishContent"
                    }
                ],
                "Default": "RejectContent"
            },
            "PublishContent": {
                "Type": "Task",
                "Resource": "arn:aws:lambda:us-east-1:123456789012:function:publish-content",
                "End": True
            },
            "RejectContent": {
                "Type": "Task",
                "Resource": "arn:aws:lambda:us-east-1:123456789012:function:handle-rejection",
                "End": True
            }
        }
    }

    response = stepfunctions.create_state_machine(
        name='genai-approval-workflow',
        definition=json.dumps(definition),
        roleArn='arn:aws:iam::123456789012:role/StepFunctionsRole',
        type='STANDARD'
    )

    print(f"State machine created: {response['stateMachineArn']}")
    return response['stateMachineArn']


def send_approval_decision(task_token, approved, reviewer_comments=""):
    """
    Send human approval decision back to Step Functions.
    Called by reviewer UI after human makes decision.
    """
    if approved:
        stepfunctions.send_task_success(
            taskToken=task_token,
            output=json.dumps({
                'approved': True,
                'method': 'human',
                'reviewer_comments': reviewer_comments,
                'timestamp': str(datetime.utcnow())
            })
        )
        print("Approval sent successfully")
    else:
        stepfunctions.send_task_success(
            taskToken=task_token,
            output=json.dumps({
                'approved': False,
                'method': 'human',
                'rejection_reason': reviewer_comments,
                'timestamp': str(datetime.utcnow())
            })
        )
        print("Rejection sent successfully")


# Lambda handler for reviewer UI
def lambda_handler(event, context):
    """
    Handle approval/rejection from reviewer UI.
    """
    body = json.loads(event['body'])

    task_token = body['taskToken']
    approved = body['approved']
    comments = body.get('comments', '')

    send_approval_decision(task_token, approved, comments)

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Decision recorded'})
    }