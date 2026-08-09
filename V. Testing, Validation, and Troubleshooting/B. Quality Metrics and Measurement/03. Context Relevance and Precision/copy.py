import boto3
import json
from typing import List, Dict
import pandas as pd

bedrock_runtime = boto3.client('bedrock-runtime')

class RAGRetrievalAnalyzer:
    """Comprehensive retrieval quality analysis for RAG pipelines."""

    def analyze_retrieval(
        self,
        test_cases: List[Dict]
    ) -> pd.DataFrame:
        """Analyze retrieval quality across test cases.

        Each test case should have:
        - question: str
        - retrieved_chunks: List[str]
        - ground_truth: str (optional, for recall)
        """

        results = []

        for case in test_cases:
            # Calculate precision
            precision_result = self._calculate_precision(
                case['question'],
                case['retrieved_chunks']
            )

            # Calculate recall if ground truth available
            recall_result = None
            if 'ground_truth' in case:
                recall_result = self._calculate_recall(
                    case['ground_truth'],
                    case['retrieved_chunks']
                )

            results.append({
                'question': case['question'][:50] + '...',
                'num_chunks': len(case['retrieved_chunks']),
                'context_precision': precision_result['precision'],
                'relevant_chunks': precision_result['relevant_count'],
                'context_recall': recall_result['recall'] if recall_result else None,
                'missing_info': len(recall_result['missing']) if recall_result else None
            })

        return pd.DataFrame(results)

    def _calculate_precision(self, question: str, chunks: List[str]) -> Dict:
        prompt = f"""For the question: "{question}"

Evaluate each chunk (1 = relevant, 0 = not relevant):
{chr(10).join([f"{i+1}. {c[:200]}..." for i, c in enumerate(chunks)])}

Return JSON: {{"relevance": [1, 0, 1, ...]}}
"""
        result = bedrock_runtime.converse(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': 100, 'temperature': 0.0}
        )

        relevance = json.loads(result['output']['message']['content'][0]['text'])['relevance']
        relevant_count = sum(relevance)

        return {
            'precision': relevant_count / len(chunks) if chunks else 0,
            'relevant_count': relevant_count
        }

    def _calculate_recall(self, ground_truth: str, chunks: List[str]) -> Dict:
        combined = "\n".join(chunks)

        prompt = f"""Ground truth answer: {ground_truth}

Retrieved context: {combined[:2000]}

What information from the ground truth is MISSING from the context?
Return JSON: {{"missing": ["info 1", "info 2"], "recall": 0.0-1.0}}
"""
        result = bedrock_runtime.converse(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': 300, 'temperature': 0.0}
        )

        return json.loads(result['output']['message']['content'][0]['text'])

    def generate_report(self, df: pd.DataFrame) -> Dict:
        """Generate summary report from analysis results."""

        return {
            'total_test_cases': len(df),
            'avg_context_precision': df['context_precision'].mean(),
            'avg_context_recall': df['context_recall'].mean() if 'context_recall' in df else None,
            'low_precision_cases': (df['context_precision'] < 0.5).sum(),
            'low_recall_cases': (df['context_recall'] < 0.5).sum() if 'context_recall' in df else None,
            'avg_chunks_retrieved': df['num_chunks'].mean()
        }