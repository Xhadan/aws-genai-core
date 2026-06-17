import boto3
import json
from dataclasses import dataclass
from typing import Generator, Optional

@dataclass
class StreamingMetrics:
    input_tokens: int = 0
    output_tokens: int = 0
    first_token_latency_ms: Optional[float] = None
    total_latency_ms: Optional[float] = None

def stream_with_metrics(
    prompt: str,
    model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
    max_tokens: int = 1024,
    temperature: float = 0.7
) -> Generator[tuple[str, Optional[StreamingMetrics]], None, None]:
    """
    Stream model response with full event handling and metrics.

    Yields:
        Tuple of (text_chunk, metrics) where metrics is populated on completion
    """
    import time

    bedrock_runtime = boto3.client('bedrock-runtime')

    start_time = time.time()
    first_token_time = None
    metrics = StreamingMetrics()

    response = bedrock_runtime.invoke_model_with_response_stream(
        modelId=model_id,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })
    )

    try:
        for event in response['body']:
            chunk = json.loads(event['chunk']['bytes'])
            event_type = chunk.get('type')

            if event_type = 'message_start':
                # Initial message metadata
                message = chunk.get('message', {})
                metrics.input_tokens = message.get('usage', {}).get('input_tokens', 0)

            elif event_type = 'content_block_delta':
                text = chunk['delta'].get('text', '')
                if text:
                    # Record first token time
                    if first_token_time is None:
                        first_token_time = time.time()
                        metrics.first_token_latency_ms = (first_token_time - start_time) * 1000

                    yield (text, None)

            elif event_type = 'message_delta':
                # Final usage stats
                usage = chunk.get('usage', {})
                metrics.output_tokens = usage.get('output_tokens', 0)

            elif event_type = 'message_stop':
                # Stream complete
                metrics.total_latency_ms = (time.time() - start_time) * 1000

                # Check for invocation metrics
                if 'amazon-bedrock-invocationMetrics' in chunk:
                    inv_metrics = chunk['amazon-bedrock-invocationMetrics']
                    metrics.first_token_latency_ms = inv_metrics.get('firstByteLatency')
                    metrics.total_latency_ms = inv_metrics.get('invocationLatency')

                yield ('', metrics)
                break

    except Exception as e:
        # Handle mid-stream errors
        print(f"Streaming error: {e}")
        raise

# Usage with metrics tracking
print("Response: ", end="", flush=True)
final_metrics = None

for chunk, metrics in stream_with_metrics("Write a haiku about programming"):
    if metrics:
        final_metrics = metrics
    else:
        print(chunk, end="", flush=True)

print(f"\n\nMetrics:")
print(f"  First token: {final_metrics.first_token_latency_ms:.0f}ms")
print(f"  Total time: {final_metrics.total_latency_ms:.0f}ms")
print(f"  Tokens: {final_metrics.input_tokens} in, {final_metrics.output_tokens} out")