import boto3
import json
from dataclasses import dataclass
from typing import List, Dict, Callable
import re

bedrock_runtime = boto3.client('bedrock-runtime')

@dataclass
class EvaluationResult:
    """Result of a single evaluation."""
    test_case_id: str
    prompt_version: str
    metrics: Dict[str, float]
    passed: bool
    details: str = ""

class GenAIEvaluator:
    """Automated evaluation for GenAI outputs."""

    def __init__(self, model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"):
        self.model_id = model_id
        self.metrics: Dict[str, Callable] = {}
        self._register_default_metrics()

    def _register_default_metrics(self):
        """Register default evaluation metrics."""
        self.metrics['length_check'] = self._check_length
        self.metrics['format_check'] = self._check_format
        self.metrics['contains_keywords'] = self._check_keywords
        self.metrics['llm_quality_score'] = self._llm_quality_score

    def _check_length(self, output: str, config: dict) -> float:
        """Check if output length is within bounds."""
        min_len = config.get('min_length', 0)
        max_len = config.get('max_length', float('inf'))
        length = len(output)
        if min_len <= length <= max_len:
            return 1.0
        return 0.0

    def _check_format(self, output: str, config: dict) -> float:
        """Check if output matches expected format."""
        format_type = config.get('format', 'any')

        if format_type = 'bullet_points':
            bullets = len(re.findall(r'^[\-\*\d]\s', output, re.MULTILINE))
            expected = config.get('expected_bullets', 3)
            return min(bullets / expected, 1.0)

        elif format_type = 'json':
            try:
                json.loads(output)
                return 1.0
            except:
                return 0.0

        return 1.0

    def _check_keywords(self, output: str, config: dict) -> float:
        """Check if output contains expected keywords."""
        keywords = config.get('keywords', [])
        if not keywords:
            return 1.0
        found = sum(1 for k in keywords if k.lower() in output.lower())
        return found / len(keywords)

    def _llm_quality_score(self, output: str, config: dict) -> float:
        """Use LLM to evaluate output quality."""
        criteria = config.get('criteria', 'accuracy, relevance, and clarity')
        reference = config.get('reference', '')

        eval_prompt = f"""Evaluate the following AI-generated output on a scale of 1-10
based on {criteria}.

Output to evaluate:
{output}

{f'Reference answer: {reference}' if reference else ''}

Respond with only a single number from 1-10."""

        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',  # Use smaller model for evaluation
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": eval_prompt}]
            })
        )

        result = json.loads(response['body'].read())
        score_text = result['content'][0]['text'].strip()

        try:
            score = float(re.search(r'\d+', score_text).group())
            return score / 10.0
        except:
            return 0.5

    def evaluate(
        self,
        test_cases: List[Dict],
        prompt_template: str,
        prompt_version: str,
        threshold: float = 0.7
    ) -> List[EvaluationResult]:
        """Run evaluation on test cases."""
        results = []

        for test_case in test_cases:
            test_id = test_case['id']
            inputs = test_case['inputs']
            eval_config = test_case.get('evaluation', {})

            # Generate output
            prompt = prompt_template.format(**inputs)
            response = bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )

            result = json.loads(response['body'].read())
            output = result['content'][0]['text']

            # Run evaluation metrics
            metrics = {}
            for metric_name, metric_config in eval_config.items():
                if metric_name in self.metrics:
                    metrics[metric_name] = self.metrics[metric_name](output, metric_config)

            # Calculate overall score
            avg_score = sum(metrics.values()) / len(metrics) if metrics else 0

            results.append(EvaluationResult(
                test_case_id=test_id,
                prompt_version=prompt_version,
                metrics=metrics,
                passed=avg_score >= threshold,
                details=f"Average score: {avg_score:.2f}"
            ))

        return results

# Example test case definition
TEST_CASES = [
    {
        "id": "summarize-001",
        "inputs": {
            "document": "The board meeting concluded with three key decisions...",
            "num_points": "3"
        },
        "evaluation": {
            "length_check": {"min_length": 100, "max_length": 500},
            "format_check": {"format": "bullet_points", "expected_bullets": 3},
            "llm_quality_score": {"criteria": "accuracy and completeness"}
        }
    }
]