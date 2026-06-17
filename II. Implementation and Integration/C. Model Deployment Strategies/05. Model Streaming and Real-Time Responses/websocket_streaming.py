import json
import boto3
import os

bedrock_runtime = boto3.client('bedrock-runtime')
apigw_management = boto3.client(
    'apigatewaymanagementapi',
    endpoint_url=os.environ.get('WEBSOCKET_ENDPOINT')
)

def websocket_stream_handler(event, context):
    """
    Handle WebSocket message and stream response back.
    """
    connection_id = event['requestContext']['connectionId']
    body = json.loads(event.get('body', '{}'))
    prompt = body.get('prompt', '')

    try:
        response = bedrock_runtime.invoke_model_with_response_stream(
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
                    # Send chunk to WebSocket client
                    apigw_management.post_to_connection(
                        ConnectionId=connection_id,
                        Data=json.dumps({
                            'type': 'content',
                            'text': text
                        }).encode()
                    )

            elif chunk['type'] = 'message_stop':
                # Send completion signal
                apigw_management.post_to_connection(
                    ConnectionId=connection_id,
                    Data=json.dumps({
                        'type': 'complete'
                    }).encode()
                )

        return {'statusCode': 200}

    except apigw_management.exceptions.GoneException:
        # Client disconnected
        print(f"Client {connection_id} disconnected")
        return {'statusCode': 200}

    except Exception as e:
        # Send error to client
        apigw_management.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps({
                'type': 'error',
                'message': str(e)
            }).encode()
        )
        return {'statusCode': 500}