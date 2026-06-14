import json
import boto3
import os
from datetime import datetime

bedrock_runtime = boto3.client('bedrock-runtime')
sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

CALLBACK_TOPIC = os.environ.get('CALLBACK_SNS_TOPIC')
JOBS_TABLE = os.environ.get('JOBS_TABLE')

def lambda_handler(event, context):
    """
    Async Lambda handler for long-running FM tasks.
    Stores results and notifies via SNS.
    """
    job_id = event.get('job_id')
    prompt = event.get('prompt')
    callback_url = event.get('callback_url')

    table = dynamodb.Table(JOBS_TABLE)

    # Update job status
    table.update_item(
        Key={'job_id': job_id},
        UpdateExpression='SET #status = :status, started_at = :started',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': 'PROCESSING',
            ':started': datetime.utcnow().isoformat()
        }
    )

    try:
        # Long-running Bedrock call
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}]
            })
        )

        result = json.loads(response['body'].read())
        output = result['content'][0]['text']

        # Store result
        table.update_item(
            Key={'job_id': job_id},
            UpdateExpression='SET #status = :status, result = :result, completed_at = :completed',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'COMPLETED',
                ':result': output,
                ':completed': datetime.utcnow().isoformat()
            }
        )

        # Notify via SNS
        sns.publish(
            TopicArnLLBACK_TOPIC,
            Message=json.dumps({
                'job_id': job_id,
                'status': 'COMPLETED',
                'callback_url': callback_url
            })
        )

        return {'status': 'COMPLETED', 'job_id': job_id}

    except Exception as e:
        # Update failure status
        table.update_item(
            Key={'job_id': job_id},
            UpdateExpression='SET #status = :status, error = :error',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'FAILED',
                ':error': str(e)
            }
        )
        raise