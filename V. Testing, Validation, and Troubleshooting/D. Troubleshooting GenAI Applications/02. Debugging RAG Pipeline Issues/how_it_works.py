import boto3
import json
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class DebugResult:
    layer: str
    status: str
    details: Dict
    suggestions: List[str]

class RAGDebugger:
    """Debug RAG pipeline issues systematically."""

    def __init__(self, kb_id: str, model_id: str):
        self.kb_id = kb_id
        self.model_id = model_id
        self.bedrock_agent = boto3.client('bedrock-agent-runtime')
        self.bedrock = boto3.client('bedrock-runtime')

    def debug_query(self, query: str) -> List[DebugResult]:
        """Run full debugging analysis on a query."""

        results = []

        # 1. Debug retrieval
        retrieval_result = self._debug_retrieval(query)
        results.append(retrieval_result)

        if retrieval_result.status = 'FAIL':
            return results  # Can't continue without retrieval

        # 2. Debug context assembly
        chunks = retrieval_result.details['chunks']
        assembly_result = self._debug_context_assembly(chunks)
        results.append(assembly_result)

        # 3. Debug generation
        context = assembly_result.details['context']
        generation_result = self._debug_generation(query, context)
        results.append(generation_result)

        return results

    def _debug_retrieval(self, query: str) -> DebugResult:
        """Debug retrieval layer."""

        response = self.bedrock_agent.retrieve(
            knowledgeBaseId=self.kb_id,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {'numberOfResults': 10}
            }
        )

        chunks = response['retrievalResults']

        if not chunks:
            return DebugResult(
                layer='retrieval',
                status='FAIL',
                details={'chunks': [], 'error': 'No chunks retrieved'},
                suggestions=[
                    'Check if knowledge base has data',
                    'Verify query matches document content',
                    'Try broader query terms'
                ]
            )

        scores = [c['score'] for c in chunks]
        avg_score = sum(scores) / len(scores)
        top_score = scores[0]

        issues = []
        suggestions = []

        if top_score < 0.5:
            issues.append(f'Low top score: {top_score:.3f}')
            suggestions.append('Consider different chunking strategy')
            suggestions.append('Try different embedding model')

        if avg_score < 0.3:
            issues.append(f'Low average score: {avg_score:.3f}')
            suggestions.append('Review document relevance to use case')

        return DebugResult(
            layer='retrieval',
            status='WARN' if issues else 'OK',
            details={
                'chunks': chunks,
                'top_score': top_score,
                'avg_score': avg_score,
                'chunk_count': len(chunks),
                'issues': issues
            },
            suggestions=suggestions
        )

    def _debug_context_assembly(self, chunks: List[Dict]) -> DebugResult:
        """Debug context assembly."""

        # Assemble context
        context_parts = [c['content']['text'] for c in chunks[:5]]
        context = '\n\n'.join(context_parts)

        # Estimate tokens (rough: 4 chars per token)
        estimated_tokens = len(context) // 4

        issues = []
        suggestions = []

        if estimated_tokens > 100000:
            issues.append(f'Context may be too long: ~{estimated_tokens} tokens')
            suggestions.append('Reduce number of chunks')
            suggestions.append('Use summarization for long chunks')

        if estimated_tokens < 100:
            issues.append('Context may be too short')
            suggestions.append('Retrieve more chunks')
            suggestions.append('Check chunk size configuration')

        # Check for chunk continuity
        if len(chunks) > 1:
            # Could check for overlapping content or source continuity
            pass

        return DebugResult(
            layer='context_assembly',
            status='WARN' if issues else 'OK',
            details={
                'context': context,
                'estimated_tokens': estimated_tokens,
                'chunks_used': len(context_parts),
                'issues': issues
            },
            suggestions=suggestions
        )

    def _debug_generation(self, query: str, context: str) -> DebugResult:
        """Debug generation layer."""

        # Generate response
        prompt = f"""Based on the following context, answer the question.
Use only information from the context. If the answer is not in the context, say so.

Context:
{context[:8000]}

Question: {query}

Answer:"""

        response = self.bedrock.converse(
            modelId=self.model_id,
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': 1024, 'temperature': 0.1}
        )

        answer = response['output']['message']['content'][0]['text']

        # Check for hallucination indicators
        issues = []
        suggestions = []

        # Simple faithfulness check
        faithfulness_check = self._quick_faithfulness_check(answer, context)

        if faithfulness_check['score'] < 0.7:
            issues.append(f"Low faithfulness: {faithfulness_check['score']:.2f}")
            suggestions.append('Strengthen grounding instructions')
            suggestions.append('Lower temperature')
            suggestions.append('Use Bedrock Guardrails with grounding')

        if 'I don\'t have' in answer or 'not in the context' in answer:
            issues.append('Model claims no information')
            suggestions.append('Review if context actually contains answer')

        return DebugResult(
            layer='generation',
            status='WARN' if issues else 'OK',
            details={
                'answer': answer,
                'faithfulness': faithfulness_check,
                'issues': issues
            },
            suggestions=suggestions
        )

    def _quick_faithfulness_check(self, answer: str, context: str) -> Dict:
        """Quick faithfulness assessment."""

        prompt = f"""Rate how well the answer is grounded in the context (0-1).
Context: {context[:2000]}
Answer: {answer[:500]}
Return only a number."""

        response = self.bedrock.converse(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': 10, 'temperature': 0.0}
        )

        try:
            score = float(response['output']['message']['content'][0]['text'].strip())
        except:
            score = 0.5

        return {'score': score}

# Usage
debugger = RAGDebugger('kb-12345', 'anthropic.claude-3-sonnet-20240229-v1:0')
results = debugger.debug_query("What is the refund policy?")

for result in results:
    print(f"\n{result.layer.upper()}: {result.status}")
    if result.suggestions:
        print("Suggestions:", result.suggestions)