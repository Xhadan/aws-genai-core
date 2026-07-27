import boto3
import asyncio
from typing import AsyncGenerator, Callable, Optional
import time

class StreamingOptimizer:
    """Optimized streaming for minimal perceived latency"""

    def __init__(self, model_id: str = 'anthropic.claude-3-haiku-20240307-v1:0'):
        self.bedrock = boto3.client('bedrock-runtime')
        self.model_id = model_id

    def stream_with_callback(
        self,
        prompt: str,
        on_token: Callable[[str], None],
        on_complete: Optional[Callable[[dict], None]] = None,
        max_tokens: int = 500
    ) -> dict:
        """
        Stream response with callback for each token chunk.
        Enables immediate display of generated content.
        """
        start_time = time.perf_counter()
        first_token_time = None
        full_response = ""
        metadata = {}

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

                # Callback with each chunk for immediate display
                on_token(chunk)

            if 'metadata' in event:
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

    def stream_with_early_stop(
        self,
        prompt: str,
        stop_condition: Callable[[str], bool],
        max_tokens: int = 500
    ) -> dict:
        """
        Stream with early stopping based on content condition.
        Useful for extracting specific information without full generation.
        """
        full_response = ""
        stopped_early = False

        response = self.bedrock.converse_stream(
            modelId=self.model_id,
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': max_tokens}
        )

        for event in response['stream']:
            if 'contentBlockDelta' in event:
                chunk = event['contentBlockDelta']['delta'].get('text', '')
                full_response += chunk

                # Check stop condition
                if stop_condition(full_response):
                    stopped_early = True
                    break

        return {
            'response': full_response,
            'stopped_early': stopped_early
        }


class ConnectionOptimizer:
    """Optimize network and connection settings for low latency"""

    def __init__(self):
        from botocore.config import Config

        # Optimized boto3 configuration
        self.config = Config(
            connect_timeout=5,
            read_timeout`,
            retries={'max_attempts': 2},
            max_pool_connections%,  # Connection pooling
            tcp_keepalive=True
        )

        self.bedrock = boto3.client(
            'bedrock-runtime',
            config=self.config
        )

    def invoke_optimized(self, model_id: str, prompt: str) -> dict:
        """Invoke with optimized connection settings"""
        return self.bedrock.converse(
            modelId=model_id,
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': 500}
        )


class LatencyOptimizationStrategies:
    """Collection of latency optimization strategies"""

    @staticmethod
    def optimize_prompt_for_latency(prompt: str, max_input_tokens: int = 1000) -> str:
        """
        Optimize prompt for lower latency.
        Larger prompts = higher TTFT.
        """
        words = prompt.split()
        if len(words) > max_input_tokens * 0.75:  # Rough word-to-token ratio
            # Truncate or summarize
            return ' '.join(words[:int(max_input_tokens * 0.75)])
        return prompt

    @staticmethod
    def select_model_for_latency(
        task_complexity: str,
        latency_budget_ms: int
    ) -> str:
        """Select model based on latency requirements"""
        # Model latency profiles (approximate TTFT)
        models = {
            'anthropic.claude-3-haiku-20240307-v1:0': {'ttft': 300, 'capability': 'low'},
            'anthropic.claude-3-5-sonnet-20241022-v2:0': {'ttft': 600, 'capability': 'high'},
            'anthropic.claude-3-opus-20240229-v1:0': {'ttft': 1200, 'capability': 'highest'}
        }

        # Filter by latency budget
        candidates = [
            (model, info) for model, info in models.items()
            if info['ttft'] < latency_budget_ms * 0.5  # Leave room for generation
        ]

        if not candidates:
            # Return fastest if budget too tight
            return 'anthropic.claude-3-haiku-20240307-v1:0'

        # Select most capable within budget
        capability_order = {'highest': 3, 'high': 2, 'low': 1}
        candidates.sort(key=lambda x: capability_order[x[1]['capability']], reverse=True)

        return candidates[0][0]


# Example: Streaming with real-time display
streamer = StreamingOptimizer()

def print_token(token):
    print(token, end='', flush=True)

def on_complete(result):
    print(f"\n\n[TTFT: {result['ttft_ms']:.0f}ms, TTLT: {result['ttlt_ms']:.0f}ms]")

result = streamer.stream_with_callback(
    prompt="List 5 benefits of cloud computing.",
    on_token=print_token,
    on_complete=on_complete
)

# Example: Early stopping
def has_three_items(text):
    return text.count('\n') >= 3 or text.count('.') >= 3

result = streamer.stream_with_early_stop(
    prompt="List 10 programming languages:",
    stop_condition=has_three_items
)
print(f"\nStopped early: {result['stopped_early']}")
print(f"Response: {result['response']}")