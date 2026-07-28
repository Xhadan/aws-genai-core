import boto3
import json
from typing import Dict, List, Optional
import time

sqs = boto3.client('sqs')
bedrock = boto3.client('bedrock-runtime')

class SQSRequestQueue:
    """Queue-based request processing for high-volume workloads"""

    def __init__(
        self,
        queue_url: str,
        dlq_url: str = None,
        max_retries: int = 3
    ):
        self.sqs = boto3.client('sqs')
        self.bedrock = boto3.client('bedrock-runtime')
        self.queue_url = queue_url
        self.dlq_url = dlq_url
        self.max_retries = max_retries

    def enqueue_request(
        self,
        prompt: str,
        model_id: str,
        request_id: str,
        priority: int = 5,
        callback_url: str = None
    ) -> str:
        """
        Add request to processing queue.

        Args:
            prompt: Prompt text
            model_id: Model to use
            request_id: Unique request identifier
            priority: 1-10 (1 = highest priority)
            callback_url: Optional webhook for result delivery
        """
        message = {
            'request_id': request_id,
            'prompt': prompt,
            'model_id': model_id,
            'callback_url': callback_url,
            'retry_count': 0,
            'enqueued_at': time.time()
        }

        response = self.sqs.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(message),
            MessageAttributes={
                'Priority': {
                    'DataType': 'Number',
                    'StringValue': str(priority)
                }
            }
        )

        return response['MessageId']

    def process_queue(
        self,
        batch_size: int = 5,
        visibility_timeout: int = 300,
        wait_time: int = 20
    ) -> List[Dict]:
        """
        Process messages from queue.
        Designed to be called from Lambda or worker process.
        """
        results = []

        # Receive messages
        response = self.sqs.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessagestch_size,
            VisibilityTimeout=visibility_timeout,
            WaitTimeSeconds=wait_time,
            MessageAttributeNames=['All']
        )

        messages = response.get('Messages', [])

        for message in messages:
            result = self._process_message(message)
            results.append(result)

            if result['success']:
                # Delete successful message
                self.sqs.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
            else:
                # Handle failure
                self._handle_failure(message, result)

        return results

    def _process_message(self, message: Dict) -> Dict:
        """Process a single message"""
        body = json.loads(message['Body'])

        try:
            # Invoke Bedrock
            response = self.bedrock.converse(
                modelId=body['model_id'],
                messages=[{'role': 'user', 'content': [{'text': body['prompt']}]}],
                inferenceConfig={'maxTokens': 500}
            )

            result = {
                'request_id': body['request_id'],
                'success': True,
                'response': response['output']['message']['content'][0]['text'],
                'usage': response.get('usage', {}),
                'processing_time': time.time() - body['enqueued_at']
            }

            # Send callback if configured
            if body.get('callback_url'):
                self._send_callback(body['callback_url'], result)

            return result

        except Exception as e:
            return {
                'request_id': body['request_id'],
                'success': False,
                'error': str(e),
                'retry_count': body.get('retry_count', 0)
            }

    def _handle_failure(self, message: Dict, result: Dict):
        """Handle failed message processing"""
        body = json.loads(message['Body'])
        retry_count = body.get('retry_count', 0) + 1

        if retry_count <= self.max_retries:
            # Re-enqueue with incremented retry count
            body['retry_count'] = retry_count
            self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(body),
                DelaySeconds=min(retry_count * 30, 900)  # Increasing delay
            )
        elif self.dlq_url:
            # Send to dead letter queue
            self.sqs.send_message(
                QueueUrl=self.dlq_url,
                MessageBody=json.dumps({
                    **body,
                    'error': result.get('error'),
                    'failed_at': time.time()
                })
            )

        # Delete from main queue
        self.sqs.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=message['ReceiptHandle']
        )

    def _send_callback(self, callback_url: str, result: Dict):
        """Send result to callback URL"""
        import requests
        try:
            requests.post(callback_url, json=result, timeout)
        except Exception as e:
            print(f"Callback failed: {e}")


# Lambda handler for queue processing
def lambda_handler(event, context):
    """Lambda function to process SQS messages"""
    queue = SQSRequestQueue(
        queue_url='https://sqs.us-east-1.amazonaws.com/123456789012/bedrock-requests',
        dlq_url='https://sqs.us-east-1.amazonaws.com/123456789012/bedrock-requests-dlq'
    )

    # Process SQS records from Lambda trigger
    results = []

    for record in event.get('Records', []):
        body = json.loads(record['body'])

        try:
            response = bedrock.converse(
                modelId=body['model_id'],
                messages=[{'role': 'user', 'content': [{'text': body['prompt']}]}],
                inferenceConfig={'maxTokens': 500}
            )

            results.append({
                'request_id': body['request_id'],
                'success': True
            })

        except Exception as e:
            results.append({
                'request_id': body['request_id'],
                'success': False,
                'error': str(e)
            })
            # Don't delete message - let it retry via visibility timeout

    return {'processed': len(results), 'results': results}