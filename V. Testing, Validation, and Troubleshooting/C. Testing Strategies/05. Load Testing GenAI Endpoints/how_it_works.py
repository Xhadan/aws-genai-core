import boto3
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List
import threading

@dataclass
class RequestResult:
    success: bool
    latency_ms: float
    input_tokens: int
    output_tokens: int
    error: str = None
    throttled: bool = False

class GenAILoadTester:
    """Load testing framework for GenAI applications."""

    def __init__(self, model_id: str, region: str = 'us-east-1'):
        self.model_id = model_id
        self.region = region
        self.results: List[RequestResult] = []
        self.lock = threading.Lock()

    def _make_request(self, prompt: str) -> RequestResult:
        """Make a single request and measure latency."""
        client = boto3.client('bedrock-runtime', region_name=self.region)

        start_time = time.time()

        try:
            response = client.converse(
                modelId=self.model_id,
                messages=[{'role': 'user', 'content': [{'text': prompt}]}],
                inferenceConfig={'maxTokens': 256}
            )

            latency = (time.time() - start_time) * 1000

            return RequestResult(
                success=True,
                latency_ms=latency,
                input_tokens=response['usage']['inputTokens'],
                output_tokens=response['usage']['outputTokens']
            )

        except client.exceptions.ThrottlingException as e:
            return RequestResult(
                successlse,
                latency_ms=(time.time() - start_time) * 1000,
                input_tokens=0,
                output_tokens=0,
                error='ThrottlingException',
                throttled=True
            )

        except Exception as e:
            return RequestResult(
                successlse,
                latency_ms=(time.time() - start_time) * 1000,
                input_tokens=0,
                output_tokens=0,
                error=str(e)
            )

    def run_load_test(
        self,
        prompts: List[str],
        concurrent_users: int,
        duration_seconds: int
    ) -> dict:
        """Run load test with specified concurrency."""

        self.results = []
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            while (time.time() - start_time) < duration_seconds:
                # Submit batch of requests
                futures = []
                for prompt in prompts[:concurrent_users]:
                    future = executor.submit(self._make_request, prompt)
                    futures.append(future)

                # Collect results
                for future in as_completed(futures):
                    result = future.result()
                    with self.lock:
                        self.results.append(result)

                # Brief pause to control rate
                time.sleep(0.1)

        return self._generate_report()

    def _generate_report(self) -> dict:
        """Generate load test report."""
        total = len(self.results)
        successful = [r for r in self.results if r.success]
        throttled = [r for r in self.results if r.throttled]

        if successful:
            latencies = [r.latency_ms for r in successful]
            tokens = [r.output_tokens for r in successful]

            return {
                'total_requests': total,
                'successful_requests': len(successful),
                'throttled_requests': len(throttled),
                'error_requests': total - len(successful),
                'success_rate': len(successful) / total,
                'throttle_rate': len(throttled) / total,
                'latency': {
                    'mean': statistics.mean(latencies),
                    'median': statistics.median(latencies),
                    'p95': sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
                    'p99': sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0,
                    'min': min(latencies),
                    'max': max(latencies)
                },
                'throughput': {
                    'requests_per_second': len(successful) / (self.results[-1].latency_ms / 1000) if successful else 0,
                    'tokens_per_minute': sum(tokens) * 60 / (len(successful) * statistics.mean(latencies) / 1000) if successful else 0
                }
            }
        else:
            return {
                'total_requests': total,
                'successful_requests': 0,
                'error': 'No successful requests'
            }

# Example usage
tester = GenAILoadTester('anthropic.claude-3-haiku-20240307-v1:0')

prompts = [
    "What is AWS Lambda?",
    "Explain S3 storage classes.",
    "How does VPC peering work?"
] * 10  # Repeat for variety

report = tester.run_load_test(
    prompts=prompts,
    concurrent_users,
    duration_seconds`
)

print(f"Success Rate: {report['success_rate']:.2%}")
print(f"Throttle Rate: {report['throttle_rate']:.2%}")
print(f"P95 Latency: {report['latency']['p95']:.0f}ms")