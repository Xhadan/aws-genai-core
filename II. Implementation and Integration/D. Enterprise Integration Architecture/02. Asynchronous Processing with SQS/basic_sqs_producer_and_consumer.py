import boto3
import json
import uuid
from datetime import datetime

sqs = boto3.client('sqs')

QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/123456789012/genai-requests"

def submit_genai_request(
    prompt: str,
    callback_url: str = None,
    priority: str = "normal",
    user_id: str = None,
    metadata: dict = None
) -> str:
    """
    Submit a GenAI request to SQS for async processing.
    Returns a request ID for tracking.
    """
    request_id = str(uuid.uuid4())

    message = {
        'request_id': request_id,
        'prompt': prompt,
        'callback_url': callback_url,
        'priority': priority,
        'user_id': user_id,
        'metadata': metadata or {},
        'submitted_at': datetime.utcnow().isoformat(),
        'model_config': {
            'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
            'max_tokens': 1024,
            'temperature': 0.7
        }
    }

    # Send to SQS
    response = sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(message),
        MessageAttributes={
            'RequestId': {
                'DataType': 'String',
                'StringValue': request_id
            },
            'Priority': {
                'DataType': 'String',
                'StringValue': priority
            }
        }
    )

    print(f"Submitted request {request_id}, MessageId: {response['MessageId']}")
    return request_id

def submit_batch_requests(prompts: list) -> list:
    """
    Submit multiple requests in a batch (up to 10).
    """
    entries = []
    request_ids = []

    for idx, prompt in enumerate(prompts[:10]):
        request_id = str(uuid.uuid4())
        request_ids.append(request_id)

        entries.append({
            'Id': str(idx),
            'MessageBody': json.dumps({
                'request_id': request_id,
                'prompt': prompt,
                'submitted_at': datetime.utcnow().isoformat()
            }),
            'MessageAttributes': {
                'RequestId': {
                    'DataType': 'String',
                    'StringValue': request_id
                }
            }
        })

    response = sqs.send_message_batch(
        QueueUrl=QUEUE_URL,
        Entries=entries
    )

    failed = response.get('Failed', [])
    if failed:
        print(f"Failed to send {len(failed)} messages")

    return request_ids

# Example usage
request_id = submit_genai_request(
    prompt="Summarize the key benefits of cloud computing",
    callback_url="https://api.example.com/webhook/genai",
    user_id="user-123"
)
print(f"Request submitted: {request_id}")