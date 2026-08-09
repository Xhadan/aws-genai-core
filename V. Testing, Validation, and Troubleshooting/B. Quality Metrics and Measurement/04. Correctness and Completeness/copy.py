import boto3
import json
from typing import Dict

bedrock_runtime = boto3.client('bedrock-runtime')

class QualityEvaluator:
    """Combined correctness and completeness evaluation."""

    def __init__(self, model_id: str = 'anthropic.claude-3-5-sonnet-20241022-v2:0'):
        self.model_id = model_id

    def evaluate(
        self,
        question: str,
        response: str,
        ground_truth: str = None
    ) -> Dict:
        """Comprehensive quality evaluation."""

        prompt = f"""Evaluate this response for correctness and completeness.

Question: {question}

Response: {response}

{"Ground Truth: " + ground_truth if ground_truth else ""}

Evaluate:

1. CORRECTNESS (are statements factually accurate?):
   - Check each factual claim for accuracy
   - Identify any errors or inaccuracies
   - Rate 0.0-1.0

2. COMPLETENESS (are all parts of the question addressed?):
   - Identify all aspects the question asks about
   - Check which aspects are covered
   - Rate 0.0-1.0

3. OVERALL QUALITY:
   - Weighted combination of correctness and completeness

Return JSON:
{{
    "correctness": {{
        "score": 0.0-1.0,
        "errors": ["error 1", ...],
        "accurate_claims": ["claim 1", ...]
    }},
    "completeness": {{
        "score": 0.0-1.0,
        "addressed": ["aspect 1", ...],
        "missing": ["aspect 1", ...]
    }},
    "overall_quality": 0.0-1.0,
    "summary": "brief assessment"
}}
"""

        result = bedrock_runtime.converse(
            modelId=self.model_id,
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': 1000, 'temperature': 0.0}
        )

        return json.loads(result['output']['message']['content'][0]['text'])

    def batch_evaluate(self, samples: list) -> Dict:
        """Evaluate multiple samples and aggregate."""

        results = []
        for sample in samples:
            eval_result = self.evaluate(
                sample['question'],
                sample['response'],
                sample.get('ground_truth')
            )
            results.append(eval_result)

        # Aggregate scores
        avg_correctness = sum(r['correctness']['score'] for r in results) / len(results)
        avg_completeness = sum(r['completeness']['score'] for r in results) / len(results)
        avg_quality = sum(r['overall_quality'] for r in results) / len(results)

        return {
            'sample_count': len(results),
            'average_correctness': avg_correctness,
            'average_completeness': avg_completeness,
            'average_quality': avg_quality,
            'below_threshold': sum(1 for r in results if r['overall_quality'] < 0.7),
            'individual_results': results
        }

# Example usage
evaluator = QualityEvaluator()

result = evaluator.evaluate(
    question="What are the main differences between SQS and SNS?",
    response="SQS is a queue service for message buffering. SNS is pub/sub for notifications.",
    ground_truth="SQS is pull-based queuing, SNS is push-based pub/sub. SQS supports one-to-one, SNS supports one-to-many."
)

print(f"Correctness: {result['correctness']['score']:.2f}")
print(f"Completeness: {result['completeness']['score']:.2f}")
print(f"Overall: {result['overall_quality']:.2f}")