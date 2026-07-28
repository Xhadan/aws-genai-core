import boto3
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, AsyncGenerator
import json

app = FastAPI()
bedrock = boto3.client('bedrock-runtime')

class ChatRequest(BaseModel):
    prompt: str
    model_id: str = 'anthropic.claude-3-haiku-20240307-v1:0'
    max_tokens: int = 1000
    system_prompt: Optional[str] = None

async def generate_sse_stream(
    prompt: str,
    model_id: str,
    max_tokens: int,
    system_prompt: str = None
) -> AsyncGenerator[str, None]:
    """
    Generate Server-Sent Events stream for client consumption.
    """
    messages = [{'role': 'user', 'content': [{'text': prompt}]}]

    params = {
        'modelId': model_id,
        'messages': messages,
        'inferenceConfig': {'maxTokens': max_tokens}
    }

    if system_prompt:
        params['system'] = [{'text': system_prompt}]

    try:
        response = bedrock.converse_stream(**params)

        for event in response['stream']:
            if 'contentBlockDelta' in event:
                chunk = event['contentBlockDelta']['delta'].get('text', '')
                # Format as SSE
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            elif 'metadata' in event:
                usage = event['metadata'].get('usage', {})
                yield f"data: {json.dumps({'type': 'metadata', 'usage': usage})}\n\n"

        # Send completion event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

@app.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    """
    Streaming chat endpoint.
    Returns Server-Sent Events stream.
    """
    return StreamingResponse(
        generate_sse_stream(
            prompt=request.prompt,
            model_id=request.model_id,
            max_tokens=request.max_tokens,
            system_prompt=request.system_prompt
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

# JavaScript client code for consuming SSE
CLIENT_JS = """
async function streamChat(prompt) {
    const response = await fetch('/chat/stream', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({prompt: prompt})
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const {done, value} = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, {stream: true});
        const lines = buffer.split('\\n\\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                if (data.type == 'token') {
                    // Append token to display
                    document.getElementById('output').innerText += data.content;
                } else if (data.type == 'done') {
                    console.log('Stream complete');
                }
            }
        }
    }
}
"""


class WebSocketStreamingHandler:
    """WebSocket-based streaming for bidirectional communication"""

    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime')

    async def handle_websocket_message(
        self,
        websocket,
        message: dict
    ):
        """
        Handle WebSocket message and stream response.
        For use with API Gateway WebSocket or FastAPI WebSocket.
        """
        prompt = message.get('prompt', '')
        model_id = message.get('model_id', 'anthropic.claude-3-haiku-20240307-v1:0')

        try:
            response = self.bedrock.converse_stream(
                modelId=model_id,
                messages=[{'role': 'user', 'content': [{'text': prompt}]}],
                inferenceConfig={'maxTokens': 1000}
            )

            for event in response['stream']:
                if 'contentBlockDelta' in event:
                    chunk = event['contentBlockDelta']['delta'].get('text', '')
                    await websocket.send_json({
                        'type': 'token',
                        'content': chunk
                    })

                elif 'metadata' in event:
                    await websocket.send_json({
                        'type': 'metadata',
                        'usage': event['metadata'].get('usage', {})
                    })

            await websocket.send_json({'type': 'done'})

        except Exception as e:
            await websocket.send_json({
                'type': 'error',
                'message': str(e)
            })


# Lambda handler for API Gateway WebSocket
def websocket_handler(event, context):
    """
    AWS Lambda handler for API Gateway WebSocket.
    Streams Bedrock response back through WebSocket connection.
    """
    import boto3

    # Get connection details
    connection_id = event['requestContext']['connectionId']
    domain = event['requestContext']['domainName']
    stage = event['requestContext']['stage']

    # Create API Gateway management client
    apigw = boto3.client(
        'apigatewaymanagementapi',
        endpoint_url=f'https://{domain}/{stage}'
    )

    bedrock = boto3.client('bedrock-runtime')

    # Parse message
    body = json.loads(event.get('body', '{}'))
    prompt = body.get('prompt', '')

    try:
        # Stream response
        response = bedrock.converse_stream(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': 1000}
        )

        for stream_event in response['stream']:
            if 'contentBlockDelta' in stream_event:
                chunk = stream_event['contentBlockDelta']['delta'].get('text', '')
                apigw.post_to_connection(
                    ConnectionId=connection_id,
                    Data=json.dumps({'type': 'token', 'content': chunk})
                )

        # Send completion
        apigw.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps({'type': 'done'})
        )

        return {'statusCode': 200}

    except Exception as e:
        apigw.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps({'type': 'error', 'message': str(e)})
        )
        return {'statusCode': 500}