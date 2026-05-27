import boto3
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import statistics

bedrock_runtime = boto3.client('bedrock-runtime')
cloudwatch = boto3.client('cloudwatch')

@dataclass
class ABTestConfig:
    """Configuration for an A/B test."""
    test_id: str
    prompt_a_arn: str
    prompt_b_arn: str
    traffic_split: float  # Percentage for version A (0-100)
    start_time: datetime
    end_time: datetime
    metrics: List[str]
    min_sample_size: int = 1000

class PromptABTester:
    """Run A/B tests on prompt versions."""

    def __init__(self, dynamodb_table: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(dynamodb_table)
        self.active_tests: Dict[str, ABTestConfig] = {}

    def create_test(self, config: ABTestConfig) -> str:
        """Create and activate an A/B test."""
        self.table.put_item(Item={
            'pk': f"TEST#{config.test_id}",
            'sk': 'CONFIG',
            'prompt_a_arn': config.prompt_a_arn,
            'prompt_b_arn': config.prompt_b_arn,
            'traffic_split': config.traffic_split,
            'start_time': config.start_time.isoformat(),
            'end_time': config.end_time.isoformat(),
            'metrics': config.metrics,
            'min_sample_size': config.min_sample_size,
            'status': 'active'
        })

        self.active_tests[config.test_id] = config
        return config.test_id

    def get_variant(self, test_id: str, user_id: str) -> str:
        """Get assigned variant for a user."""
        config = self.active_tests.get(test_id)
        if not config:
            raise ValueError(f"Test {test_id} not found")

        # Consistent hashing for user assignment
        hash_input = f"{test_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        bucket = hash_value % 100

        if bucket < config.traffic_split:
            return 'A', config.prompt_a_arn
        else:
            return 'B', config.prompt_b_arn

    def invoke_with_test(self, test_id: str, user_id: str,
                         input_data: Dict) -> Dict:
        """Invoke the appropriate variant and track results."""
        variant, prompt_arn = self.get_variant(test_id, user_id)
        start_time = datetime.utcnow()

        # Invoke the prompt (simplified - actual implementation would use prompt ARN)
        response = bedrock_runtime.converse(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            messages=[{"role": "user", "content": [{"text": json.dumps(input_data)}]}],
            inferenceConfig={"maxTokens": 1024}
        )

        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000

        # Record result
        result = {
            'test_id': test_id,
            'variant': variant,
            'user_id': user_id,
            'latency_ms': latency_ms,
            'response': response['output']['message']['content'][0]['text'],
            'timestamp': datetime.utcnow().isoformat(),
            'input_tokens': response['usage']['inputTokens'],
            'output_tokens': response['usage']['outputTokens']
        }

        self._record_result(result)

        return result

    def record_feedback(self, test_id: str, user_id: str,
                        quality_score: float, feedback: str = ""):
        """Record user feedback for a test result."""
        variant, _ = self.get_variant(test_id, user_id)

        self.table.put_item(Item={
            'pk': f"TEST#{test_id}",
            'sk': f"FEEDBACK#{user_id}#{datetime.utcnow().isoformat()}",
            'variant': variant,
            'quality_score': quality_score,
            'feedback': feedback,
            'timestamp': datetime.utcnow().isoformat()
        })

    def get_test_results(self, test_id: str) -> Dict:
        """Get aggregated test results."""
        # Get all results for this test
        results_a = self._get_variant_results(test_id, 'A')
        results_b = self._get_variant_results(test_id, 'B')

        analysis = {
            'test_id': test_id,
            'sample_size_a': len(results_a),
            'sample_size_b': len(results_b),
            'metrics': {
                'latency': {
                    'A': self._calculate_stats([r['latency_ms'] for r in results_a]),
                    'B': self._calculate_stats([r['latency_ms'] for r in results_b])
                },
                'quality_score': {
                    'A': self._calculate_stats([r.get('quality_score', 0) for r in results_a if 'quality_score' in r]),
                    'B': self._calculate_stats([r.get('quality_score', 0) for r in results_b if 'quality_score' in r])
                },
                'tokens': {
                    'A': self._calculate_stats([r['output_tokens'] for r in results_a]),
                    'B': self._calculate_stats([r['output_tokens'] for r in results_b])
                }
            },
            'statistical_significance': self._calculate_significance(results_a, results_b)
        }

        return analysis

    def declare_winner(self, test_id: str) -> Dict:
        """Analyze results and declare a winner."""
        results = self.get_test_results(test_id)

        # Check sample size
        config = self.active_tests.get(test_id)
        if (results['sample_size_a'] < config.min_sample_size or
            results['sample_size_b'] < config.min_sample_size):
            return {'status': 'insufficient_data', 'results': results}

        # Check statistical significance
        if not results['statistical_significance']['significant']:
            return {'status': 'not_significant', 'results': results}

        # Determine winner based on quality score
        quality_a = results['metrics']['quality_score']['A']['mean']
        quality_b = results['metrics']['quality_score']['B']['mean']

        winner = 'A' if quality_a > quality_b else 'B'

        return {
            'status': 'complete',
            'winner': winner,
            'improvement': abs(quality_a - quality_b) / min(quality_a, quality_b) * 100,
            'results': results
        }

    def _record_result(self, result: Dict):
        """Store test result."""
        self.table.put_item(Item={
            'pk': f"TEST#{result['test_id']}",
            'sk': f"RESULT#{result['variant']}#{result['timestamp']}",
            **result
        })

    def _get_variant_results(self, test_id: str, variant: str) -> List[Dict]:
        """Get all results for a variant."""
        response = self.table.query(
            KeyConditionExpression="pk = :pk AND begins_with(sk, :prefix)",
            ExpressionAttributeValues={
                ':pk': f"TEST#{test_id}",
                ':prefix': f"RESULT#{variant}#"
            }
        )
        return response['Items']

    def _calculate_stats(self, values: List[float]) -> Dict:
        """Calculate statistics for a list of values."""
        if not values:
            return {'mean': 0, 'median': 0, 'std': 0, 'p95': 0}

        sorted_values = sorted(values)
        p95_index = int(len(sorted_values) * 0.95)

        return {
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std': statistics.stdev(values) if len(values) > 1 else 0,
            'p95': sorted_values[p95_index] if p95_index < len(sorted_values) else sorted_values[-1]
        }

    def _calculate_significance(self, results_a: List, results_b: List) -> Dict:
        """Calculate statistical significance (simplified t-test)."""
        if len(results_a) < 30 or len(results_b) < 30:
            return {'significant': False, 'reason': 'insufficient_sample'}

        # Simplified - use proper statistical test in production
        scores_a = [r.get('quality_score', 0) for r in results_a if 'quality_score' in r]
        scores_b = [r.get('quality_score', 0) for r in results_b if 'quality_score' in r]

        if len(scores_a) < 30 or len(scores_b) < 30:
            return {'significant': False, 'reason': 'insufficient_feedback'}

        mean_diff = abs(statistics.mean(scores_a) - statistics.mean(scores_b))
        pooled_std = (statistics.stdev(scores_a) + statistics.stdev(scores_b)) / 2

        # Simplified effect size check
        effect_size = mean_diff / pooled_std if pooled_std > 0 else 0

        return {
            'significant': effect_size > 0.2,  # Small effect size threshold
            'effect_size': effect_size
        }


# Example usage
tester = PromptABTester("ab-tests")

# Create test
config = ABTestConfig(
    test_id="support-v2-test",
    prompt_a_arn="arn:aws:bedrock:...:prompt/support:1",
    prompt_b_arn="arn:aws:bedrock:...:prompt/support:2",
    traffic_splitP,
    start_timetetime.utcnow(),
    end_timetetime.utcnow(),  # Would be future date
    metrics=["quality_score", "latency", "tokens"],
    min_sample_size00
)

test_id = tester.create_test(config)
print(f"Created test: {test_id}")