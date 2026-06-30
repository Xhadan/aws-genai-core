import boto3
import json
from typing import Generator
from dataclasses import dataclass

bedrock_runtime = boto3.client('bedrock-runtime')

@dataclass
class StreamMetrics:
    first_byte_latency_ms: int = 0
    invocation_latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

def stream_claude_response(
    prompt: str,
    model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
    max_tokens: int = 1024
) -> Generator[tuple[str, StreamMetrics], None, None]:
    """
    Stream Claude response with detailed event handling.
    Yields (text_chunk, metrics) tuples.
    """

    response = bedrock_runtime.invoke_model_with_response_stream(
        modelId=model_id,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        })
    )

    metrics = StreamMetrics()

    for event in response['body']:
        chunk = json.loads(event['chunk']['bytes'])
        event_type = chunk.get('type')

        if event_type = 'message_start':
            # Initial message metadata
            message = chunk.get('message', {})
            usage = message.get('usage', {})
            metrics.input_tokens = usage.get('input_tokens', 0)

        elif event_type = 'content_block_start':
            # New content block beginning
            pass

        elif event_type = 'content_block_delta':
            # Actual content tokens
            delta = chunk.get('delta', {})
            text = delta.get('text', '')
            if text:
                yield (text, None)

        elif event_type = 'content_block_stop':
            # Content block ended
            pass

        elif event_type = 'message_delta':
            # Final message metadata
            usage = chunk.get('usage', {})
            metrics.output_tokens = usage.get('output_tokens', 0)

        elif event_type = 'message_stop':
            # Stream complete - extract metrics
            inv_metrics = chunk.get('amazon-bedrock-invocationMetrics', {})
            metrics.first_byte_latency_ms = inv_metrics.get('firstByteLatency', 0)
            metrics.invocation_latency_ms = inv_metrics.get('invocationLatency', 0)

            yield ('', metrics)
            break

# Usage with metrics tracking
print("Response: ", end="", flush=True)
final_metrics = None

for text, metrics in stream_claude_response("Write a haiku about clouds."):
    if metrics:
        final_metrics = metrics
    else:
        print(text, end="", flush=True)

print(f"\n\nMetrics:")
print(f"  First byte: {final_metrics.first_byte_latency_ms}ms")
print(f"  Total: {final_metrics.invocation_latency_ms}ms")
print(f"  Tokens: {final_metrics.input_tokens} in, {final_metrics.output_tokens} out")