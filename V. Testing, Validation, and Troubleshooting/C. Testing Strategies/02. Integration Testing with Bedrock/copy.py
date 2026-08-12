import boto3
import pytest
import json
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class TestResult:
    query: str
    response: str
    relevance_score: float
    keyword_match: bool
    citation_present: bool
    latency_ms: float

class IntegrationTestSuite:
    """Comprehensive integration test suite with quality gates."""

    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent-runtime')
        self.results: List[TestResult] = []

    def run_test_suite(
        self,
        test_cases: List[Dict],
        kb_id: str,
        model_id: str
    ) -> Dict:
        """Run complete test suite and return quality report."""

        import time

        for case in test_cases:
            start = time.time()

            response = self.bedrock_agent.retrieve_and_generate(
                input={'text': case['query']},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': kb_id,
                        'modelArn': f'arn:aws:bedrock:us-east-1::foundation-model/{model_id}'
                    }
                }
            )

            latency = (time.time() - start) * 1000

            generated_text = response['output']['text']

            # Evaluate result
            result = TestResult(
                queryse['query'],
                response=generated_text[:500],
                relevance_score=self._calculate_relevance(case['query'], generated_text),
                keyword_match=self._check_keywords(generated_text, case.get('keywords', [])),
                citation_present=len(response.get('citations', [])) > 0,
                latency_ms=latency
            )

            self.results.append(result)

        return self._generate_report()

    def _calculate_relevance(self, query: str, response: str) -> float:
        """Calculate semantic relevance score."""
        # Simplified - in practice use embedding similarity
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        overlap = len(query_words & response_words)
        return min(1.0, overlap / max(len(query_words), 1) * 2)

    def _check_keywords(self, response: str, keywords: List[str]) -> bool:
        """Check if required keywords are present."""
        if not keywords:
            return True
        return any(kw.lower() in response.lower() for kw in keywords)

    def _generate_report(self) -> Dict:
        """Generate quality report with pass/fail determination."""

        total = len(self.results)

        # Calculate metrics
        avg_relevance = sum(r.relevance_score for r in self.results) / total
        keyword_match_rate = sum(1 for r in self.results if r.keyword_match) / total
        citation_rate = sum(1 for r in self.results if r.citation_present) / total
        avg_latency = sum(r.latency_ms for r in self.results) / total
        p95_latency = sorted([r.latency_ms for r in self.results])[int(total * 0.95)]

        # Quality gates
        quality_gates = {
            'relevance': avg_relevance >= 0.6,
            'keyword_coverage': keyword_match_rate >= 0.8,
            'citations': citation_rate >= 0.9,
            'latency_p95': p95_latency < 5000  # 5 second SLA
        }

        all_passed = all(quality_gates.values())

        return {
            'total_tests': total,
            'metrics': {
                'average_relevance': avg_relevance,
                'keyword_match_rate': keyword_match_rate,
                'citation_rate': citation_rate,
                'average_latency_ms': avg_latency,
                'p95_latency_ms': p95_latency
            },
            'quality_gates': quality_gates,
            'all_gates_passed': all_passed,
            'failed_tests': [
                {'query': r.query, 'relevance': r.relevance_score}
                for r in self.results if r.relevance_score < 0.5
            ]
        }

# Usage in pytest
@pytest.fixture(scope="module")
def integration_suite():
    return IntegrationTestSuite()

def test_rag_quality_gates(integration_suite):
    """Integration test with quality gates."""

    test_cases = [
        {'query': 'What is Lambda?', 'keywords': ['serverless', 'function']},
        {'query': 'S3 storage classes', 'keywords': ['Standard', 'Glacier']},
        {'query': 'EC2 instance types', 'keywords': ['compute', 'instance']}
    ]

    report = integration_suite.run_test_suite(
        test_cases=test_cases,
        kb_id='test-kb-id',
        model_id='anthropic.claude-3-sonnet-20240229-v1:0'
    )

    assert report['all_gates_passed'], f"Quality gates failed: {report['quality_gates']}"