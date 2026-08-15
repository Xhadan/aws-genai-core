import boto3
import time
import json
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor
import threading

class QualityAwareLoadTest:
    """Load test that also monitors response quality."""

    def __init__(self, model_id: str, judge_model: str = 'anthropic.claude-3-haiku-20240307-v1:0'):
        self.model_id = model_id
        self.judge_model = judge_model
        self.bedrock = boto3.client('bedrock-runtime')

    def run_test(
        self,
        test_queries: List[Dict],
        concurrent_users: int,
        duration_seconds: int
    ) -> Dict:
        """Run load test while monitoring quality."""

        results = []
        lock = threading.Lock()
        start_time = time.time()

        def process_query(query: Dict):
            while (time.time() - start_time) < duration_seconds:
                req_start = time.time()

                try:
                    # Make request
                    response = self.bedrock.converse(
                        modelId=self.model_id,
                        messages=[{'role': 'user', 'content': [{'text': query['text']}]}],
                        inferenceConfig={'maxTokens': 256}
                    )

                    latency = (time.time() - req_start) * 1000
                    generated_text = response['output']['message']['content'][0]['text']

                    # Sample quality evaluation (1 in 10 requests)
                    quality_score = None
                    if len(results) % 10 = 0:
                        quality_score = self._evaluate_quality(query['text'], generated_text)

                    with lock:
                        results.append({
                            'success': True,
                            'latency': latency,
                            'quality_score': quality_score,
                            'tokens': response['usage']['outputTokens']
                        })

                except Exception as e:
                    with lock:
                        results.append({
                            'success': False,
                            'latency': (time.time() - req_start) * 1000,
                            'error': str(e)
                        })

        # Run concurrent load
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for i in range(concurrent_users):
                query = test_queries[i % len(test_queries)]
                futures.append(executor.submit(process_query, query))

            for f in futures:
                f.result()

        return self._generate_report(results)

    def _evaluate_quality(self, query: str, response: str) -> float:
        """Quick quality evaluation."""
        try:
            result = self.bedrock.converse(
                modelId=self.judge_model,
                messages=[{
                    'role': 'user',
                    'content': [{'text': f"Rate 0-1: Q:{query[:100]} A:{response[:200]}"}]
                }],
                inferenceConfig={'maxTokens': 10, 'temperature': 0.0}
            )
            return float(result['output']['message']['content'][0]['text'].strip())
        except:
            return None

    def _generate_report(self, results: List[Dict]) -> Dict:
        """Generate report with quality metrics."""
        successful = [r for r in results if r['success']]
        latencies = [r['latency'] for r in successful]
        quality_scores = [r['quality_score'] for r in successful if r.get('quality_score')]

        import statistics

        return {
            'total_requests': len(results),
            'success_rate': len(successful) / len(results),
            'latency': {
                'mean': statistics.mean(latencies) if latencies else 0,
                'p95': sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 10 else 0
            },
            'quality': {
                'samples_evaluated': len(quality_scores),
                'mean_quality': statistics.mean(quality_scores) if quality_scores else None,
                'min_quality': min(quality_scores) if quality_scores else None
            }
        }