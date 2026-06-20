import boto3
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sqs = boto3.client('sqs')
bedrock_runtime = boto3.client('bedrock-runtime')

class RateLimitedProcessor:
    """
    Process SQS messages with controlled rate to avoid Bedrock throttling.
    """

    def __init__(
        self,
        queue_url: str,
        requests_per_minute: int = 60,
        max_workers: int = 5
    ):
        self.queue_url = queue_url
        self.requests_per_minute = requests_per_minute
        self.max_workers = max_workers
        self.interval = 60.0 / requests_per_minute

    def process_messages(self, duration_seconds: int = 300):
        """
        Process messages for specified duration with rate limiting.
        """
        start_time = time.time()
        processed_count = 0
        last_request_time = 0

        while time.time() - start_time < duration_seconds:
            # Rate limiting
            elapsed = time.time() - last_request_time
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)

            # Receive messages
            response = sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=1,  # One at a time for rate control
                WaitTimeSeconds=5,
                VisibilityTimeout00
            )

            messages = response.get('Messages', [])
            if not messages:
                continue

            last_request_time = time.time()

            for message in messages:
                try:
                    result = self._process_single(message)
                    processed_count += 1

                    # Delete successful message
                    sqs.delete_message(
                        QueueUrl=self.queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )

                except Exception as e:
                    print(f"Error: {e}")
                    # Message will return to queue after visibility timeout

        return processed_count

    def _process_single(self, message: dict) -> dict:
        """Process a single message."""
        body = json.loads(message['Body'])

        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": body['prompt']}]
            })
        )

        result = json.loads(response['body'].read())
        return {
            'request_id': body['request_id'],
            'response': result['content'][0]['text']
        }

# Usage
processor = RateLimitedProcessor(
    queue_url="https://sqs.us-east-1.amazonaws.com/123456789012/genai-requests",
    requests_per_minute0  # Conservative rate
)

processed = processor.process_messages(duration_seconds`0)
print(f"Processed {processed} messages")