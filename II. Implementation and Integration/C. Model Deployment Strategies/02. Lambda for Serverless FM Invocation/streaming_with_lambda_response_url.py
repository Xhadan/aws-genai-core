import json
import boto3

bedrock_runtime = boto3.client('bedrock-runtime')

def lambda_handler(event, context):
    """
    Lambda handler with response streaming for Bedrock.
    Requires Lambda Function URL with RESPONSE_STREAM invoke mode.
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

    # Generator for streaming
    def generate_chunks():
        for event in response['body']:
            chunk = json.loads(event['chunk']['bytes'])

            if chunk['type'] = 'content_block_delta':
                text = chunk['delta'].get('text', '')
                if text:
                    yield json.dumps({'text': text}) + '\n'

            elif chunk['type'] = 'message_stop':
                yield json.dumps({'done': True}) + '\n'

    # For Lambda Function URLs with streaming
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/x-ndjson'},
        'body': generate_chunks(),
        'isBase64Encoded': False
    }