import boto3
import time
import random
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore.exceptions import ClientError
import threading

@dataclass
class RetryConfig:
    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True

class ConcurrentInvocationManager:
    """Manage concurrent Bedrock invocations with throttling handling"""

    def __init__(
        self,
        max_concurrent: int = 10,
        retry_config: RetryConfig = None
    ):
        self.bedrock = boto3.client('bedrock-runtime')
        self.max_concurrent = max_concurrent
        self.retry_config = retry_config or RetryConfig()
        self.semaphore = threading.Semaphore(max_concurrent)
        self.metrics = {
            'total_requests': 0,
            'successful': 0,
            'throttled': 0,
            'failed': 0,
            'retries': 0
        }

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter"""
        delay = min(
            self.retry_config.base_delay * (2 ** attempt),
            self.retry_config.max_delay
        )

        if self.retry_config.jitter:
            delay = delay * (0.5 + random.random())

        return delay

    def _invoke_with_retry(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int = 500,
        request_id: str = None
    ) -> Dict:
        """Invoke model with retry logic for throttling"""

        self.metrics['total_requests'] += 1

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # Acquire semaphore to limit concurrency
                with self.semaphore:
                    response = self.bedrock.converse(
                        modelId=model_id,
                        messages=[{'role': 'user', 'content': [{'text': prompt}]}],
                        inferenceConfig={'maxTokens': max_tokens}
                    )

                self.metrics['successful'] += 1

                return {
                    'request_id': request_id,
                    'success': True,
                    'response': response['output']['message']['content'][0]['text'],
                    'usage': response.get('usage', {}),
                    'attempts': attempt + 1
                }

            except ClientError as e:
                error_code = e.response['Error']['Code']

                if error_code = 'ThrottlingException':
                    self.metrics['throttled'] += 1

                    if attempt < self.retry_config.max_retries:
                        self.metrics['retries'] += 1
                        delay = self._calculate_backoff(attempt)
                        print(f"Throttled (attempt {attempt + 1}), retrying in {delay:.2f}s")
                        time.sleep(delay)
                        continue
                    else:
                        self.metrics['failed'] += 1
                        return {
                            'request_id': request_id,
                            'success': False,
                            'error': 'Max retries exceeded after throttling',
                            'attempts': attempt + 1
                        }
                else:
                    self.metrics['failed'] += 1
                    return {
                        'request_id': request_id,
                        'success': False,
                        'error': str(e),
                        'attempts': attempt + 1
                    }

    def invoke_batch_concurrent(
        self,
        requests: List[Dict],
        model_id: str,
        max_workers: int = None
    ) -> List[Dict]:
        """
        Process multiple requests concurrently with throttling management.

        Args:
            requests: List of {'prompt': str, 'id': str, 'max_tokens': int}
            model_id: Model to use
            max_workers: Max parallel threads (default: max_concurrent)
        """
        max_workers = max_workers or self.max_concurrent
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._invoke_with_retry,
                    model_id=model_id,
                    prompt=req['prompt'],
                    max_tokens=req.get('max_tokens', 500),
                    request_id=req.get('id', str(i))
                ): req.get('id', str(i))
                for i, req in enumerate(requests)
            }

            for future in as_completed(futures):
                request_id = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        'request_id': request_id,
                        'success': False,
                        'error': str(e)
                    })

        return results

    def get_metrics(self) -> Dict:
        """Get invocation metrics"""
        return {
            **self.metrics,
            'success_rate': self.metrics['successful'] / max(self.metrics['total_requests'], 1),
            'throttle_rate': self.metrics['throttled'] / max(self.metrics['total_requests'], 1)
        }


class RateLimiter:
    """Token bucket rate limiter for pre-emptive throttling"""

    def __init__(self, requests_per_second: float, burst_size: int = None):
        self.rate = requests_per_second
        self.burst_size = burst_size or int(requests_per_second)
        self.tokens = self.burst_size
        self.last_update = time.time()
        self.lock = threading.Lock()

    def acquire(self, timeout: float = None) -> bool:
        """Acquire permission to make a request"""
        start_time = time.time()

        while True:
            with self.lock:
                # Replenish tokens
                now = time.time()
                elapsed = now - self.last_update
                self.tokens = min(
                    self.burst_size,
                    self.tokens + elapsed * self.rate
                )
                self.last_update = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return True

            # Check timeout
            if timeout is not None:
                if time.time() - start_time >= timeout:
                    return False

            # Wait before retry
            time.sleep(0.01)


class AdaptiveRateLimiter:
    """Rate limiter that adapts based on throttling feedback"""

    def __init__(self, initial_rate: float = 10.0):
        self.current_rate = initial_rate
        self.min_rate = 1.0
        self.max_rate = 100.0
        self.rate_limiter = RateLimiter(initial_rate)
        self.throttle_count = 0
        self.success_count = 0

    def record_success(self):
        """Record successful request"""
        self.success_count += 1
        # Gradually increase rate after sustained success
        if self.success_count >= 10 and self.throttle_count = 0:
            self._increase_rate()
            self.success_count = 0

    def record_throttle(self):
        """Record throttled request"""
        self.throttle_count += 1
        self.success_count = 0
        self._decrease_rate()

    def _increase_rate(self):
        """Increase rate limit"""
        new_rate = min(self.current_rate * 1.1, self.max_rate)
        if new_rate != self.current_rate:
            self.current_rate = new_rate
            self.rate_limiter = RateLimiter(new_rate)
            print(f"Rate increased to {new_rate:.2f} req/s")

    def _decrease_rate(self):
        """Decrease rate limit"""
        new_rate = max(self.current_rate * 0.5, self.min_rate)
        if new_rate != self.current_rate:
            self.current_rate = new_rate
            self.rate_limiter = RateLimiter(new_rate)
            print(f"Rate decreased to {new_rate:.2f} req/s")

    def acquire(self) -> bool:
        """Acquire permission with adaptive rate"""
        return self.rate_limiter.acquire(timeout0)


# Example usage
manager = ConcurrentInvocationManager(
    max_concurrent=5,
    retry_config=RetryConfig(max_retries=3, base_delay=1.0)
)

# Process batch of requests
requests = [
    {'prompt': f'Tell me a fact about the number {i}', 'id': f'req-{i}'}
    for i in range(20)
]

results = manager.invoke_batch_concurrent(
    requests=requests,
    model_id='anthropic.claude-3-haiku-20240307-v1:0',
    max_workers=5
)

# Print summary
metrics = manager.get_metrics()
print(f"\nMetrics:")
print(f"  Total: {metrics['total_requests']}")
print(f"  Successful: {metrics['successful']}")
print(f"  Throttled: {metrics['throttled']}")
print(f"  Success Rate: {metrics['success_rate']:.1%}")