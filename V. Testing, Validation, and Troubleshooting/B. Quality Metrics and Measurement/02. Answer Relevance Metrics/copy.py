import boto3
import json
from typing import List, Dict
import pandas as pd

bedrock_runtime = boto3.client('bedrock-runtime')

class RelevanceAnalyzer:
    """Analyze answer relevance at scale."""

    def __init__(self):
        self.results = []

    def evaluate_batch(
        self,
        qa_pairs: List[Dict]
    ) -> pd.DataFrame:
        """Evaluate relevance for a batch of Q&A pairs."""

        for pair in qa_pairs:
            result = self.evaluate_single(
                pair['question'],
                pair['answer'],
                pair.get('id')
            )
            self.results.append(result)

        return pd.DataFrame(self.results)

    def evaluate_single(
        self,
        question: str,
        answer: str,
        sample_id: str = None
    ) -> Dict:
        """Evaluate a single Q&A pair."""

        prompt = f"""Rate answer relevance to question (0.0 to 1.0):
Question: {question}
Answer: {answer}

Return only JSON: {{"relevance": 0.0-1.0, "issues": ["issue1", ...]}}
"""

        result = bedrock_runtime.converse(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': 200, 'temperature': 0.0}
        )

        eval_result = json.loads(result['output']['message']['content'][0]['text'])

        return {
            'id': sample_id,
            'question': question[:100],
            'relevance': eval_result['relevance'],
            'issues': eval_result.get('issues', []),
            'needs_review': eval_result['relevance'] < 0.7
        }

    def generate_report(self) -> Dict:
        """Generate analysis report."""

        df = pd.DataFrame(self.results)

        return {
            'total_samples': len(df),
            'average_relevance': df['relevance'].mean(),
            'median_relevance': df['relevance'].median(),
            'below_threshold': (df['relevance'] < 0.7).sum(),
            'above_threshold': (df['relevance'] >= 0.7).sum(),
            'common_issues': self._get_common_issues(df)
        }

    def _get_common_issues(self, df: pd.DataFrame) -> Dict[str, int]:
        """Count common issues across all samples."""
        all_issues = []
        for issues in df['issues']:
            all_issues.extend(issues)

        from collections import Counter
        return dict(Counter(all_issues).most_common(5))

# Example usage
analyzer = RelevanceAnalyzer()

qa_pairs = [
    {'id': '1', 'question': 'What is Lambda?', 'answer': 'Lambda is serverless compute...'},
    {'id': '2', 'question': 'S3 pricing?', 'answer': 'S3 pricing is based on storage, requests...'},
]

results_df = analyzer.evaluate_batch(qa_pairs)
report = analyzer.generate_report()
print(f"Average Relevance: {report['average_relevance']:.3f}")