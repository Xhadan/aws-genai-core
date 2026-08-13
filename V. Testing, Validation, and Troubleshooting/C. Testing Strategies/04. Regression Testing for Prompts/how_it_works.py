import boto3
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np

@dataclass
class RegressionResult:
    query: str
    baseline_response: str
    new_response: str
    baseline_score: float
    new_score: float
    regressed: bool
    score_delta: float

class GenAIRegressionTester:
    """Framework for GenAI regression testing."""

    def __init__(self, baseline_path: str, tolerance: float = 0.05):
        self.baseline_path = baseline_path
        self.tolerance = tolerance
        self.bedrock = boto3.client('bedrock-runtime')
        self.baseline = self._load_baseline()

    def _load_baseline(self) -> Dict:
        """Load baseline metrics and responses."""
        with open(self.baseline_path, 'r') as f:
            return json.load(f)

    def run_regression_test(
        self,
        new_config: Dict,
        test_queries: List[Dict]
    ) -> Dict:
        """Run regression test comparing new config against baseline."""

        results = []

        for query in test_queries:
            # Get baseline result
            baseline_result = self.baseline['results'].get(query['id'])

            # Run with new config
            new_response = self._invoke_model(new_config, query['text'])

            # Evaluate quality
            new_score = self._evaluate_quality(query['text'], new_response)
            baseline_score = baseline_result['score'] if baseline_result else 0

            # Check for regression
            regressed = new_score < (baseline_score - self.tolerance)

            results.append(RegressionResult(
                query=query['text'][:100],
                baseline_responseseline_result['response'][:200] if baseline_result else '',
                new_response=new_response[:200],
                baseline_scoreseline_score,
                new_score=new_score,
                regressed=regressed,
                score_delta=new_score - baseline_score
            ))

        return self._generate_report(results)

    def _invoke_model(self, config: Dict, query: str) -> str:
        """Invoke model with given configuration."""
        response = self.bedrock.converse(
            modelId=config['model_id'],
            messages=[{'role': 'user', 'content': [{'text': query}]}],
            system=[{'text': config.get('system_prompt', '')}] if config.get('system_prompt') else [],
            inferenceConfig={
                'temperature': config.get('temperature', 0.7),
                'maxTokens': config.get('max_tokens', 1024)
            }
        )
        return response['output']['message']['content'][0]['text']

    def _evaluate_quality(self, query: str, response: str) -> float:
        """Evaluate response quality using LLM-as-Judge."""
        eval_prompt = f"""Rate this response quality 0-1.
Query: {query}
Response: {response}
Return only a number between 0 and 1."""

        result = self.bedrock.converse(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            messages=[{'role': 'user', 'content': [{'text': eval_prompt}]}],
            inferenceConfig={'maxTokens': 10, 'temperature': 0.0}
        )

        try:
            return float(result['output']['message']['content'][0]['text'].strip())
        except:
            return 0.5

    def _generate_report(self, results: List[RegressionResult]) -> Dict:
        """Generate regression test report."""

        total = len(results)
        regressions = sum(1 for r in results if r.regressed)
        improvements = sum(1 for r in results if r.score_delta > self.tolerance)

        baseline_mean = np.mean([r.baseline_score for r in results])
        new_mean = np.mean([r.new_score for r in results])

        # Statistical test
        from scipy import stats
        _, p_value = stats.ttest_rel(
            [r.baseline_score for r in results],
            [r.new_score for r in results]
        )

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_tests': total,
            'regressions': regressions,
            'improvements': improvements,
            'unchanged': total - regressions - improvements,
            'baseline_mean': baseline_mean,
            'new_mean': new_mean,
            'mean_delta': new_mean - baseline_mean,
            'p_value': p_value,
            'statistically_significant': p_value < 0.05,
            'passed': regressions = 0 or (regressions / total) < 0.1,
            'regressed_queries': [
                {'query': r.query, 'delta': r.score_delta}
                for r in results if r.regressed
            ]
        }

# Example usage
tester = GenAIRegressionTester('baseline_v1.2.json', tolerance=0.05)

new_config = {
    'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
    'system_prompt': 'You are a helpful AWS assistant.',
    'temperature': 0.5
}

test_queries = [
    {'id': 'q1', 'text': 'What is S3?'},
    {'id': 'q2', 'text': 'How does Lambda pricing work?'},
    {'id': 'q3', 'text': 'Explain VPC peering'}
]

report = tester.run_regression_test(new_config, test_queries)
print(f"Passed: {report['passed']}")
print(f"Regressions: {report['regressions']}/{report['total_tests']}")