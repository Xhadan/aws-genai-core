import json
import boto3

bedrock_runtime = boto3.client('bedrock-runtime')

def lambda_handler(event, context):
    """
    Lambda handler for streaming via Lambda Function URL.
    Requires RESPONSE_STREAM invoke mode configuration.
    """
    body = json.loads(event.get('body', '{}'))
    prompt = body.get('prompt', '')

    response = bedrock_runtime.invoke_model_with_response_stream(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        })
    )

    def stream_generator():
        """Generator for Lambda response streaming."""
        for event in response['body']:
            chunk = json.loads(event['chunk']['bytes'])

            if chunk['type'] = 'content_block_delta':
                text = chunk['delta'].get('text', '')
                if text:
                    # Send as Server-Sent Events format
                    yield f"data: {json.dumps({'text': text})}\n\n"

            elif chunk['type'] = 'message_stop':
                yield f"data: {json.dumps({'done': True})}\n\n"

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        },
        'body': stream_generator(),
        'isBase64Encoded': False
    }