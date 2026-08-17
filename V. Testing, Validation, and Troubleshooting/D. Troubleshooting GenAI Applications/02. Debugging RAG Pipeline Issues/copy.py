import boto3
from typing import List, Dict

class RetrievalAnalyzer:
    """Analyze retrieval quality for debugging."""

    def __init__(self, kb_id: str):
        self.kb_id = kb_id
        self.bedrock_agent = boto3.client('bedrock-agent-runtime')

    def analyze_retrieval(
        self,
        query: str,
        expected_topics: List[str] = None
    ) -> Dict:
        """Analyze retrieval quality for a query."""

        response = self.bedrock_agent.retrieve(
            knowledgeBaseId=self.kb_id,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {'numberOfResults': 10}
            }
        )

        chunks = response['retrievalResults']

        analysis = {
            'query': query,
            'chunks_retrieved': len(chunks),
            'score_distribution': self._analyze_scores(chunks),
            'source_distribution': self._analyze_sources(chunks),
            'topic_coverage': None,
            'issues': [],
            'recommendations': []
        }

        # Check for issues
        if not chunks:
            analysis['issues'].append('No chunks retrieved')
            analysis['recommendations'].append('Verify knowledge base contains relevant documents')
        elif chunks[0]['score'] < 0.5:
            analysis['issues'].append(f"Low top relevance score: {chunks[0]['score']:.3f}")
            analysis['recommendations'].append('Consider query reformulation')
            analysis['recommendations'].append('Review chunking strategy')

        # Check topic coverage if expected topics provided
        if expected_topics:
            analysis['topic_coverage'] = self._check_topic_coverage(
                chunks, expected_topics
            )
            if analysis['topic_coverage']['missing']:
                analysis['issues'].append(
                    f"Missing topics: {analysis['topic_coverage']['missing']}"
                )

        return analysis

    def _analyze_scores(self, chunks: List[Dict]) -> Dict:
        """Analyze score distribution."""
        if not chunks:
            return {'mean': 0, 'max': 0, 'min': 0}

        scores = [c['score'] for c in chunks]
        return {
            'mean': sum(scores) / len(scores),
            'max': max(scores),
            'min': min(scores),
            'above_0.7': sum(1 for s in scores if s > 0.7),
            'below_0.3': sum(1 for s in scores if s < 0.3)
        }

    def _analyze_sources(self, chunks: List[Dict]) -> Dict:
        """Analyze source distribution."""
        sources = {}
        for chunk in chunks:
            source = chunk.get('location', {}).get('s3Location', {}).get('uri', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        return sources

    def _check_topic_coverage(
        self,
        chunks: List[Dict],
        expected_topics: List[str]
    ) -> Dict:
        """Check if expected topics are covered."""
        combined_text = ' '.join(c['content']['text'].lower() for c in chunks)

        found = []
        missing = []

        for topic in expected_topics:
            if topic.lower() in combined_text:
                found.append(topic)
            else:
                missing.append(topic)

        return {
            'found': found,
            'missing': missing,
            'coverage_ratio': len(found) / len(expected_topics) if expected_topics else 0
        }

# Usage
analyzer = RetrievalAnalyzer('kb-12345')
analysis = analyzer.analyze_retrieval(
    query="What is the return policy?",
    expected_topics=["refund", "30 days", "receipt"]
)
print(f"Issues: {analysis['issues']}")
print(f"Recommendations: {analysis['recommendations']}")