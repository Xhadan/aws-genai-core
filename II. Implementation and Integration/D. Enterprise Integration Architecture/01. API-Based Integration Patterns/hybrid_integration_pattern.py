import json
import boto3
import os

# REST endpoint for initiating requests
def rest_handler(event, context):
    """
    REST handler that initiates streaming via WebSocket.
    Returns connection info for client to receive streamed response.
    """
    body = json.loads(event.get('body', '{}'))
    request_id = context.aws_request_id

    # Store request in DynamoDB for WebSocket handler
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['REQUESTS_TABLE'])

    table.put_item(Item={
        'request_id': request_id,
        'prompt': body.get('prompt'),
        'status': 'pending',
        'created_at': int(time.time())
    })

    return {
        'statusCode': 202,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'request_id': request_id,
            'websocket_url': os.environ['WEBSOCKET_URL'],
            'message': 'Subscribe to WebSocket with request_id to receive response'
        })
    }

# WebSocket connection handler
def websocket_connect(event, context):
    """Handle WebSocket connection."""
    connection_id = event['requestContext']['connectionId']

    # Store connection
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['CONNECTIONS_TABLE'])

    table.put_item(Item={
        'connection_id': connection_id,
        'connected_at': int(time.time())
    })

    return {'statusCode': 200}

# WebSocket message handler with streaming
def websocket_message(event, context):
    """Handle WebSocket message and stream Bedrock response."""
    connection_id = event['requestContext']['connectionId']
    body = json.loads(event.get('body', '{}'))
    prompt = body.get('prompt')

    apigw = boto3.client(
        'apigatewaymanagementapi',
        endpoint_url=os.environ['WEBSOCKET_ENDPOINT']
    )

    bedrock = boto3.client('bedrock-runtime')

    # Stream response
    response = bedrock.invoke_model_with_response_stream(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        })
    )

    for event in response['body']:
        chunk = json.loads(event['chunk']['bytes'])

        if chunk['type'] = 'content_block_delta':
            text = chunk['delta'].get('text', '')
            if text:
                apigw.post_to_connection(
                    ConnectionId=connection_id,
                    Data=json.dumps({'type': 'chunk', 'text': text}).encode()
                )

        elif chunk['type'] = 'message_stop':
            apigw.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps({'type': 'done'}).encode()
            )

    return {'statusCode': 200}