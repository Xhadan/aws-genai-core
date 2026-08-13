import boto3
import json
from typing import Dict, List
from datetime import datetime

bedrock_runtime = boto3.client('bedrock-runtime')

class QualityABTest:
    """A/B testing with LLM-as-Judge quality evaluation."""

    def __init__(self, judge_model: str = 'anthropic.claude-3-5-sonnet-20241022-v2:0'):
        self.judge_model = judge_model

    def evaluate_response_quality(
        self,
        question: str,
        response: str
    ) -> Dict:
        """Use LLM-as-Judge to evaluate response quality."""

        prompt = f"""Evaluate the quality of this response on a scale of 1-10.

Question: {question}
Response: {response}

Rate on these dimensions:
1. Relevance: Does it address the question?
2. Completeness: Does it cover all aspects?
3. Clarity: Is it well-organized and clear?
4. Helpfulness: Would this help the user?

Return JSON:
{{
    "relevance": 1-10,
    "completeness": 1-10,
    "clarity": 1-10,
    "helpfulness": 1-10,
    "overall": 1-10,
    "reasoning": "brief explanation"
}}
"""

        result = bedrock_runtime.converse(
            modelId=self.judge_model,
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': 300, 'temperature': 0.0}
        )

        return json.loads(result['output']['message']['content'][0]['text'])

    def run_comparison(
        self,
        test_questions: List[str],
        variant_a_config: Dict,
        variant_b_config: Dict
    ) -> Dict:
        """Run quality comparison between two variants."""

        results = {
            'A': {'scores': [], 'latencies': []},
            'B': {'scores': [], 'latencies': []}
        }

        for question in test_questions:
            # Run variant A
            start = datetime.utcnow()
            response_a = self._invoke_variant(variant_a_config, question)
            latency_a = (datetime.utcnow() - start).total_seconds() * 1000
            quality_a = self.evaluate_response_quality(question, response_a)

            results['A']['scores'].append(quality_a['overall'])
            results['A']['latencies'].append(latency_a)

            # Run variant B
            start = datetime.utcnow()
            response_b = self._invoke_variant(variant_b_config, question)
            latency_b = (datetime.utcnow() - start).total_seconds() * 1000
            quality_b = self.evaluate_response_quality(question, response_b)

            results['B']['scores'].append(quality_b['overall'])
            results['B']['latencies'].append(latency_b)

        # Calculate summary
        import numpy as np

        return {
            'variant_a': {
                'avg_quality': np.mean(results['A']['scores']),
                'avg_latency': np.mean(results['A']['latencies'])
            },
            'variant_b': {
                'avg_quality': np.mean(results['B']['scores']),
                'avg_latency': np.mean(results['B']['latencies'])
            },
            'quality_winner': 'A' if np.mean(results['A']['scores']) > np.mean(results['B']['scores']) else 'B',
            'sample_count': len(test_questions)
        }

    def _invoke_variant(self, config: Dict, question: str) -> str:
        """Invoke model with variant configuration."""
        response = bedrock_runtime.converse(
            modelId=config['model_id'],
            messages=[{'role': 'user', 'content': [{'text': question}]}],
            system=[{'text': config.get('system_prompt', '')}] if config.get('system_prompt') else [],
            inferenceConfig={'temperature': config.get('temperature', 0.7)}
        )
        return response['output']['message']['content'][0]['text']

# Example usage
quality_test = QualityABTest()

comparison = quality_test.run_comparison(
    test_questions=[
        "Explain S3 storage classes",
        "How does Lambda pricing work?",
        "What is VPC peering?"
    ],
    variant_a_config={
        'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
        'system_prompt': 'You are a helpful assistant.',
        'temperature': 0.7
    },
    variant_b_config={
        'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
        'system_prompt': 'You are an AWS expert. Provide detailed technical answers.',
        'temperature': 0.3
    }
)

print(f"Quality Winner: Variant {comparison['quality_winner']}")