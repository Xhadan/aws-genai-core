import boto3
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import statistics

@dataclass
class LatencyMetrics:
    ttft: float  # Time to first token (ms)
    ttlt: float  # Time to last token (ms)
    token_rate: float  # Tokens per second
    input_tokens: int
    output_tokens: int
    model_id: str

class LatencyOptimizedClient:
    """Client optimized for low-latency GenAI invocations"""

    def __init__(self, region_name: str = None):
        self.bedrock = boto3.client('bedrock-runtime', region_name=region_name)
        self.metrics_history: List[LatencyMetrics] = []

    def invoke_with_latency_tracking(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int = 500,
        stream: bool = True
    ) -> Dict:
        """
        Invoke model with detailed latency tracking.

        Returns response with latency metrics.
        """
        start_time = time.perf_counter()
        first_token_time = None
        response_text = ""
        output_token_count = 0

        if stream:
            # Streaming invocation for TTFT measurement
            response = self.bedrock.converse_stream(
                modelId=model_id,
                messages=[{'role': 'user', 'content': [{'text': prompt}]}],
                inferenceConfig={'maxTokens': max_tokens}
            )

            for event in response['stream']:
                if 'contentBlockDelta' in event:
                    if first_token_time is None:
                        first_token_time = time.perf_counter()
                    chunk = event['contentBlockDelta']['delta'].get('text', '')
                    response_text += chunk
                    output_token_count += len(chunk.split())  # Rough estimate

                if 'metadata' in event:
                    usage = event['metadata'].get('usage', {})
                    output_token_count = usage.get('outputTokens', output_token_count)

        else:
            # Non-streaming invocation
            response = self.bedrock.converse(
                modelId=model_id,
                messages=[{'role': 'user', 'content': [{'text': prompt}]}],
                inferenceConfig={'maxTokens': max_tokens}
            )
            first_token_time = time.perf_counter()  # Approximate TTFT
            response_text = response['output']['message']['content'][0]['text']
            usage = response.get('usage', {})
            output_token_count = usage.get('outputTokens', len(response_text.split()))

        end_time = time.perf_counter()

        # Calculate metrics
        ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else 0
        ttlt_ms = (end_time - start_time) * 1000
        generation_time = ttlt_ms - ttft_ms
        token_rate = (output_token_count / (generation_time / 1000)) if generation_time > 0 else 0

        metrics = LatencyMetrics(
            ttft=ttft_ms,
            ttlt=ttlt_ms,
            token_rate=token_rate,
            input_tokens=len(prompt.split()),  # Rough estimate
            output_tokens=output_token_count,
            model_id=model_id
        )

        self.metrics_history.append(metrics)

        return {
            'response': response_text,
            'metrics': metrics
        }

    def benchmark_models(
        self,
        models: List[str],
        test_prompt: str,
        iterations: int = 5
    ) -> Dict[str, Dict]:
        """
        Benchmark multiple models for latency comparison.
        """
        results = {}

        for model_id in models:
            model_metrics = []

            for i in range(iterations):
                result = self.invoke_with_latency_tracking(
                    model_id=model_id,
                    prompt=test_prompt,
                    stream=True
                )
                model_metrics.append(result['metrics'])
                time.sleep(1)  # Avoid rate limiting

            # Calculate statistics
            ttft_values = [m.ttft for m in model_metrics]
            ttlt_values = [m.ttlt for m in model_metrics]
            token_rates = [m.token_rate for m in model_metrics]

            results[model_id] = {
                'ttft_p50': statistics.median(ttft_values),
                'ttft_p99': max(ttft_values),
                'ttlt_p50': statistics.median(ttlt_values),
                'ttlt_p99': max(ttlt_values),
                'avg_token_rate': statistics.mean(token_rates)
            }

        return results

    def get_latency_report(self) -> Dict:
        """Generate latency report from collected metrics"""
        if not self.metrics_history:
            return {}

        ttft_values = [m.ttft for m in self.metrics_history]
        ttlt_values = [m.ttlt for m in self.metrics_history]

        return {
            'total_requests': len(self.metrics_history),
            'ttft': {
                'p50': statistics.median(ttft_values),
                'p95': sorted(ttft_values)[int(len(ttft_values) * 0.95)] if len(ttft_values) > 1 else ttft_values[0],
                'p99': sorted(ttft_values)[int(len(ttft_values) * 0.99)] if len(ttft_values) > 1 else ttft_values[0],
                'avg': statistics.mean(ttft_values)
            },
            'ttlt': {
                'p50': statistics.median(ttlt_values),
                'p95': sorted(ttlt_values)[int(len(ttlt_values) * 0.95)] if len(ttlt_values) > 1 else ttlt_values[0],
                'p99': sorted(ttlt_values)[int(len(ttlt_values) * 0.99)] if len(ttlt_values) > 1 else ttlt_values[0],
                'avg': statistics.mean(ttlt_values)
            }
        }


# Example usage
client = LatencyOptimizedClient(region_name='us-east-1')

# Single request with metrics
result = client.invoke_with_latency_tracking(
    model_id='anthropic.claude-3-haiku-20240307-v1:0',
    prompt='Explain quantum computing in one paragraph.',
    stream=True
)

print(f"TTFT: {result['metrics'].ttft:.0f}ms")
print(f"TTLT: {result['metrics'].ttlt:.0f}ms")
print(f"Token Rate: {result['metrics'].token_rate:.1f} tok/s")

# Benchmark multiple models
models = [
    'anthropic.claude-3-haiku-20240307-v1:0',
    'anthropic.claude-3-5-sonnet-20241022-v2:0'
]

benchmark_results = client.benchmark_models(
    models=models,
    test_prompt='Write a haiku about cloud computing.',
    iterations=3
)

for model, metrics in benchmark_results.items():
    print(f"\n{model}:")
    print(f"  TTFT p50: {metrics['ttft_p50']:.0f}ms")
    print(f"  TTLT p50: {metrics['ttlt_p50']:.0f}ms")