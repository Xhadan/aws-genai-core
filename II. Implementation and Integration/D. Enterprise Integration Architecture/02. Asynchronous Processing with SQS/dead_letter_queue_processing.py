import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

def dlq_handler(event, context):
    """
    Process messages that failed all retries from DLQ.
    Log failures and notify for manual intervention.
    """
    results_table = dynamodb.Table('genai-results')
    failures_table = dynamodb.Table('genai-failures')

    for record in event['Records']:
        body = json.loads(record['body'])
        request_id = body.get('request_id', 'unknown')

        # Get failure context
        attributes = record.get('attributes', {})
        receive_count = attributes.get('ApproximateReceiveCount')
        first_receive = attributes.get('ApproximateFirstReceiveTimestamp')

        # Store detailed failure record
        failures_table.put_item(Item={
            'request_id': request_id,
            'original_message': body,
            'message_id': record['messageId'],
            'receive_count': receive_count,
            'first_receive_timestamp': first_receive,
            'dlq_received_at': datetime.utcnow().isoformat(),
            'sqs_attributes': attributes
        })

        # Update request status
        results_table.update_item(
            Key={'request_id': request_id},
            UpdateExpression='SET #status = :status, dlq_at = :dlq_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'dead_letter',
                ':dlq_at': datetime.utcnow().isoformat()
            }
        )

        # Notify operations team
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:123456789012:genai-alerts',
            Subject='GenAI Request Failed - DLQ',
            Message=json.dumps({
                'request_id': request_id,
                'prompt_preview': body.get('prompt', '')[:100],
                'receive_count': receive_count,
                'action_required': 'Manual review needed'
            }, indent=2)
        )

    return {'processed': len(event['Records'])}

def reprocess_dlq_messages(dlq_url: str, main_queue_url: str, limit: int = 10):
    """
    Utility to move messages from DLQ back to main queue after fixing issues.
    """
    sqs = boto3.client('sqs')
    processed = 0

    while processed < limit:
        response = sqs.receive_message(
            QueueUrl=dlq_url,
            MaxNumberOfMessages=min(10, limit - processed),
            WaitTimeSeconds=5
        )

        messages = response.get('Messages', [])
        if not messages:
            break

        for msg in messages:
            # Send to main queue
            sqs.send_message(
                QueueUrl=main_queue_url,
                MessageBody=msg['Body']
            )

            # Delete from DLQ
            sqs.delete_message(
                QueueUrl=dlq_url,
                ReceiptHandle=msg['ReceiptHandle']
            )

            processed += 1

    return processed