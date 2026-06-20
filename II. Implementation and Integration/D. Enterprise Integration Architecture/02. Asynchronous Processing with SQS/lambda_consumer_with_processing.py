import json
import boto3
import os
from datetime import datetime

bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

RESULTS_TABLE = os.environ.get('RESULTS_TABLE', 'genai-results')
CALLBACK_TOPIC = os.environ.get('CALLBACK_TOPIC')

def lambda_handler(event, context):
    """
    Process GenAI requests from SQS queue.
    Handles batch of messages with proper error handling.
    """
    results_table = dynamodb.Table(RESULTS_TABLE)
    batch_item_failures = []

    for record in event['Records']:
        message_id = record['messageId']

        try:
            # Parse message
            body = json.loads(record['body'])
            request_id = body['request_id']
            prompt = body['prompt']
            model_config = body.get('model_config', {})
            callback_url = body.get('callback_url')

            print(f"Processing request {request_id}")

            # Update status to processing
            results_table.update_item(
                Key={'request_id': request_id},
                UpdateExpression='SET #status = :status, started_at = :started',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'processing',
                    ':started': datetime.utcnow().isoformat()
                }
            )

            # Invoke Bedrock
            response = bedrock_runtime.invoke_model(
                modelId=model_config.get('model_id', 'anthropic.claude-3-sonnet-20240229-v1:0'),
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": model_config.get('max_tokens', 1024),
                    "temperature": model_config.get('temperature', 0.7),
                    "messages": [{"role": "user", "content": prompt}]
                })
            )

            result = json.loads(response['body'].read())
            output_text = result['content'][0]['text']
            usage = result.get('usage', {})

            # Store result
            results_table.put_item(Item={
                'request_id': request_id,
                'status': 'completed',
                'result': output_text,
                'usage': usage,
                'completed_at': datetime.utcnow().isoformat(),
                'ttl': int(datetime.utcnow().timestamp()) + 86400 * 7  # 7 day TTL
            })

            # Send callback notification if configured
            if callback_url and CALLBACK_TOPIC:
                sns.publish(
                    TopicArnLLBACK_TOPIC,
                    Message=json.dumps({
                        'request_id': request_id,
                        'status': 'completed',
                        'callback_url': callback_url
                    })
                )

            print(f"Completed request {request_id}")

        except bedrock_runtime.exceptions.ThrottlingException as e:
            # Throttling - let message return to queue for retry
            print(f"Throttled: {message_id}, will retry")
            batch_item_failures.append({'itemIdentifier': message_id})

        except Exception as e:
            print(f"Error processing {message_id}: {e}")

            # Check if this is final retry (from approximate receive count)
            receive_count = int(record.get('attributes', {}).get('ApproximateReceiveCount', 0))
            if receive_count >= 3:
                # Final retry failed - mark as failed
                try:
                    body = json.loads(record['body'])
                    results_table.put_item(Item={
                        'request_id': body.get('request_id'),
                        'status': 'failed',
                        'error': str(e),
                        'failed_at': datetime.utcnow().isoformat()
                    })
                except:
                    pass
            else:
                # Return to queue for retry
                batch_item_failures.append({'itemIdentifier': message_id})

    # Return failures for partial batch failure handling
    return {'batchItemFailures': batch_item_failures}