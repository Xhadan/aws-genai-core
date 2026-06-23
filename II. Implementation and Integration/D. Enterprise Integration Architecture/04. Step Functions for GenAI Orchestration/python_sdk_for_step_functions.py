import boto3
import json
from datetime import datetime

sfn = boto3.client('stepfunctions')

def start_genai_workflow(
    state_machine_arn: str,
    input_data: dict,
    execution_name: str = None
) -> dict:
    """Start a Step Functions workflow execution."""

    if not execution_name:
        execution_name = f"genai-{datetime.utcnow().strftime('%Y%m%d-%H%M%S-%f')}"

    response = sfn.start_execution(
        stateMachineArn=state_machine_arn,
        name=execution_name,
        input=json.dumps(input_data)
    )

    return {
        'executionArn': response['executionArn'],
        'startDate': response['startDate'].isoformat()
    }

def get_workflow_status(execution_arn: str) -> dict:
    """Get current status of workflow execution."""

    response = sfn.describe_execution(executionArn=execution_arn)

    result = {
        'status': response['status'],
        'startDate': response['startDate'].isoformat()
    }

    if response['status'] in ['SUCCEEDED', 'FAILED', 'TIMED_OUT', 'ABORTED']:
        result['stopDate'] = response.get('stopDate', '').isoformat() if response.get('stopDate') else None
        result['output'] = json.loads(response.get('output', '{}'))

    if response['status'] = 'FAILED':
        result['error'] = response.get('error')
        result['cause'] = response.get('cause')

    return result

def send_task_success(task_token: str, output: dict):
    """Send success callback for waitForTaskToken pattern."""
    sfn.send_task_success(
        taskToken=task_token,
        output=json.dumps(output)
    )

def send_task_failure(task_token: str, error: str, cause: str):
    """Send failure callback for waitForTaskToken pattern."""
    sfn.send_task_failure(
        taskToken=task_token,
        error=error,
        causeuse
    )

# Lambda handler for approval callback
def approval_callback_handler(event, context):
    """Handle approval response and callback to Step Functions."""

    body = json.loads(event.get('body', '{}'))
    task_token = body.get('taskToken')
    status = body.get('status')  # approved, rejected, revision_requested
    feedback = body.get('feedback', '')

    if status = 'approved':
        send_task_success(task_token, {
            'status': 'approved',
            'approvedBy': body.get('approver'),
            'approvedAt': datetime.utcnow().isoformat()
        })
    elif status = 'rejected':
        send_task_success(task_token, {
            'status': 'rejected',
            'reason': feedback
        })
    elif status = 'revision_requested':
        send_task_success(task_token, {
            'status': 'revision_requested',
            'feedback': feedback
        })
    else:
        send_task_failure(task_token, 'InvalidStatus', f'Unknown status: {status}')

    return {'statusCode': 200}