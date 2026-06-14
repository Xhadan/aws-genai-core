import json
import boto3
import os
from typing import Any

# Initialize client OUTSIDE handler to reuse across invocations
bedrock_runtime = boto3.client('bedrock-runtime')

# Configuration from environment
MODEL_ID = os.environ.get('MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '1024'))

def lambda_handler(event: dict, context: Any) -> dict:
    """
    Lambda handler for Bedrock model invocation.
    Handles API Gateway events with proper error handling.
    """
    try:
        # Parse input
        body = json.loads(event.get('body', '{}'))
        prompt = body.get('prompt', '')

        if not prompt:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'prompt is required'})
            }

        # Check remaining time for timeout handling
        remaining_time_ms = context.get_remaining_time_in_millis()
        if remaining_time_ms < 5000:  # Less than 5 seconds
            return {
                'statusCode': 503,
                'body': json.dumps({'error': 'Insufficient time remaining'})
            }

        # Invoke Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": MAX_TOKENS,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            })
        )

        # Parse response
        result = json.loads(response['body'].read())
        output_text = result['content'][0]['text']

        # Include usage metrics
        usage = result.get('usage', {})

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'response': output_text,
                'usage': usage
            })
        }

    except bedrock_runtime.exceptions.ThrottlingException:
        return {
            'statusCode': 429,
            'body': json.dumps({'error': 'Rate limit exceeded. Please retry.'})
        }
    except bedrock_runtime.exceptions.ModelTimeoutException:
        return {
            'statusCode': 504,
            'body': json.dumps({'error': 'Model timeout. Try shorter prompt.'})
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }