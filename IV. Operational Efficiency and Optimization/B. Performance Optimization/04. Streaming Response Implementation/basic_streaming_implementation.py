import boto3
import json
from typing import Callable, Dict, Optional, Generator
import time

class StreamingBedrockClient:
    """Client for streaming GenAI responses"""

    def __init__(self, model_id: str = 'anthropic.claude-3-haiku-20240307-v1:0'):
        self.bedrock = boto3.client('bedrock-runtime')
        self.model_id = model_id

    def stream_response(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Generator[Dict, None, None]:
        """
        Stream response tokens as generator.
        Yields event dictionaries for each chunk.
        """
        messages = [{'role': 'user', 'content': [{'text': prompt}]}]

        params = {
            'modelId': self.model_id,
            'messages': messages,
            'inferenceConfig': {
                'maxTokens': max_tokens,
                'temperature': temperature
            }
        }

        if system_prompt:
            params['system'] = [{'text': system_prompt}]

        response = self.bedrock.converse_stream(**params)

        for event in response['stream']:
            yield event

    def stream_with_callbacks(
        self,
        prompt: str,
        on_token: Callable[[str], None],
        on_start: Optional[Callable[[], None]] = None,
        on_complete: Optional[Callable[[Dict], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        max_tokens: int = 1000
    ) -> Dict:
        """
        Stream with callback functions for each event.
        Returns final metadata including usage.
        """
        start_time = time.perf_counter()
        first_token_time = None
        full_response = ""
        metadata = {}

        try:
            if on_start:
                on_start()

            response = self.bedrock.converse_stream(
                modelId=self.model_id,
                messages=[{'role': 'user', 'content': [{'text': prompt}]}],
                inferenceConfig={'maxTokens': max_tokens}
            )

            for event in response['stream']:
                if 'contentBlockDelta' in event:
                    if first_token_time is None:
                        first_token_time = time.perf_counter()

                    chunk = event['contentBlockDelta']['delta'].get('text', '')
                    full_response += chunk
                    on_token(chunk)

                elif 'metadata' in event:
                    metadata = event['metadata']

            end_time = time.perf_counter()

            result = {
                'response': full_response,
                'ttft_ms': (first_token_time - start_time) * 1000 if first_token_time else 0,
                'ttlt_ms': (end_time - start_time) * 1000,
                'usage': metadata.get('usage', {})
            }

            if on_complete:
                on_complete(result)

            return result

        except Exception as e:
            if on_error:
                on_error(e)
            raise

    def stream_with_early_cancel(
        self,
        prompt: str,
        should_cancel: Callable[[str], bool],
        max_tokens: int = 1000
    ) -> Dict:
        """
        Stream with ability to cancel based on content.
        Useful for detecting off-topic or problematic responses early.
        """
        full_response = ""
        cancelled = False

        response = self.bedrock.converse_stream(
            modelId=self.model_id,
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': max_tokens}
        )

        for event in response['stream']:
            if 'contentBlockDelta' in event:
                chunk = event['contentBlockDelta']['delta'].get('text', '')
                full_response += chunk

                # Check cancellation condition
                if should_cancel(full_response):
                    cancelled = True
                    break

        return {
            'response': full_response,
            'cancelled': cancelled
        }


class StreamingResponseAggregator:
    """Aggregate streaming responses for processing"""

    def __init__(self):
        self.chunks = []
        self.start_time = None
        self.first_token_time = None
        self.end_time = None

    def on_start(self):
        """Called when streaming starts"""
        self.start_time = time.perf_counter()
        self.chunks = []

    def on_token(self, token: str):
        """Called for each token"""
        if self.first_token_time is None:
            self.first_token_time = time.perf_counter()
        self.chunks.append(token)

    def on_complete(self, metadata: Dict):
        """Called when streaming completes"""
        self.end_time = time.perf_counter()

    def get_full_response(self) -> str:
        """Get aggregated response"""
        return ''.join(self.chunks)

    def get_metrics(self) -> Dict:
        """Get timing metrics"""
        return {
            'ttft_ms': (self.first_token_time - self.start_time) * 1000 if self.first_token_time else 0,
            'ttlt_ms': (self.end_time - self.start_time) * 1000 if self.end_time else 0,
            'chunks_received': len(self.chunks)
        }


# Example usage
client = StreamingBedrockClient()

# Simple streaming with print
def print_token(token):
    print(token, end='', flush=True)

print("Response: ", end='')
result = client.stream_with_callbacks(
    prompt="Explain cloud computing in 3 sentences.",
    on_token=print_token
)
print(f"\n\nTTFT: {result['ttft_ms']:.0f}ms, TTLT: {result['ttlt_ms']:.0f}ms")

# Generator-based streaming
print("\nGenerator streaming:")
for event in client.stream_response("Write a haiku about AWS."):
    if 'contentBlockDelta' in event:
        print(event['contentBlockDelta']['delta'].get('text', ''), end='', flush=True)
print()

# Early cancellation example
def should_cancel(response):
    # Cancel if response seems to be going off-topic
    off_topic_indicators = ['I cannot', 'I apologize', 'As an AI']
    return any(indicator in response for indicator in off_topic_indicators)

result = client.stream_with_early_cancel(
    prompt="Tell me about cloud computing.",
    should_cancel=should_cancel
)
if result['cancelled']:
    print("Response was cancelled early")