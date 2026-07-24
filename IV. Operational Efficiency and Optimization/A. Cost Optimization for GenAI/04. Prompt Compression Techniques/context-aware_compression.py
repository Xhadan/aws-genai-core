import boto3
import json
from typing import List, Dict
import numpy as np

class RAGContextCompressor:
    """Compress RAG contexts while preserving query-relevant information"""

    def __init__(self, embedding_model='amazon.titan-embed-text-v1'):
        self.bedrock = boto3.client('bedrock-runtime')
        self.embedding_model = embedding_model

    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text"""
        response = self.bedrock.invoke_model(
            modelId=self.embedding_model,
            body=json.dumps({'inputText': text})
        )
        result = json.loads(response['body'].read())
        return np.array(result['embedding'])

    def sentence_relevance_scores(
        self,
        query: str,
        sentences: List[str]
    ) -> List[float]:
        """Score sentences by relevance to query"""
        query_embedding = self.get_embedding(query)

        scores = []
        for sent in sentences:
            sent_embedding = self.get_embedding(sent)
            # Cosine similarity
            similarity = np.dot(query_embedding, sent_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(sent_embedding)
            )
            scores.append(similarity)

        return scores

    def compress_context(
        self,
        query: str,
        context: str,
        target_compression: float = 0.5,
        min_score_threshold: float = 0.3
    ) -> str:
        """
        Compress context keeping query-relevant sentences.

        Args:
            query: User query for relevance scoring
            context: Context text to compress
            target_compression: Target compression ratio (0.5 = keep 50%)
            min_score_threshold: Minimum relevance score to keep
        """
        import re

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', context)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 2:
            return context

        # Score sentences by query relevance
        scores = self.sentence_relevance_scores(query, sentences)

        # Combine sentences with scores
        scored_sentences = list(zip(sentences, scores))

        # Filter by minimum threshold
        relevant = [(s, score) for s, score in scored_sentences
                   if score >= min_score_threshold]

        if not relevant:
            # If nothing passes threshold, keep top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            keep_count = max(1, int(len(sentences) * target_compression))
            relevant = scored_sentences[:keep_count]

        # Sort by original order and keep target percentage
        target_count = max(1, int(len(sentences) * target_compression))
        relevant.sort(key=lambda x: x[1], reverse=True)
        kept = relevant[:target_count]

        # Reconstruct in original order
        kept_set = set(s for s, _ in kept)
        result = ' '.join(s for s in sentences if s in kept_set)

        return result

    def compress_multiple_contexts(
        self,
        query: str,
        contexts: List[str],
        total_token_budget: int = 2000
    ) -> List[Dict]:
        """
        Compress multiple contexts to fit within budget.
        Returns contexts with compression metadata.
        """
        # First, score entire contexts for relevance
        context_scores = [
            np.mean(self.sentence_relevance_scores(query, [ctx]))
            for ctx in contexts
        ]

        # Allocate budget proportionally to relevance
        total_score = sum(context_scores)
        if total_score = 0:
            # Equal allocation if no relevance signal
            allocations = [total_token_budget // len(contexts)] * len(contexts)
        else:
            allocations = [
                int((score / total_score) * total_token_budget)
                for score in context_scores
            ]

        results = []
        for ctx, allocation, score in zip(contexts, allocations, context_scores):
            original_tokens = len(ctx.split())

            if original_tokens <= allocation:
                # No compression needed
                results.append({
                    'content': ctx,
                    'compressed': False,
                    'original_tokens': original_tokens,
                    'final_tokens': original_tokens,
                    'relevance_score': score
                })
            else:
                # Compress to fit allocation
                target_ratio = allocation / original_tokens
                compressed = self.compress_context(
                    query, ctx,
                    target_compression=target_ratio
                )
                results.append({
                    'content': compressed,
                    'compressed': True,
                    'original_tokens': original_tokens,
                    'final_tokens': len(compressed.split()),
                    'relevance_score': score
                })

        return results


# Example usage
compressor = RAGContextCompressor()

query = "What are the return policy details?"

contexts = [
    """Our return policy allows customers to return most items within 30 days
    of purchase for a full refund. Items must be in original packaging and
    unused condition. Some exclusions apply including electronics opened
    after purchase and personalized items. Refunds are processed within
    5-7 business days.""",

    """We offer free shipping on orders over $50. Standard shipping takes
    3-5 business days. Express shipping is available for an additional fee
    and arrives within 1-2 business days. International shipping rates vary
    by destination country.""",

    """Customer satisfaction is our top priority. If you're not happy with
    your purchase, our support team is available 24/7 to help. You can
    reach us by phone, email, or live chat. Most issues are resolved
    within 24 hours."""
]

compressed = compressor.compress_multiple_contexts(
    query=query,
    contexts=contexts,
    total_token_budget0
)

for i, result in enumerate(compressed):
    print(f"\nContext {i+1}:")
    print(f"  Relevance: {result['relevance_score']:.3f}")
    print(f"  Compressed: {result['compressed']}")
    print(f"  Tokens: {result['original_tokens']} -> {result['final_tokens']}")
    print(f"  Content: {result['content'][:100]}...")