import boto3
import numpy as np
import hashlib
import time
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import redis

class OptimizedRAGRetrieval:
    """High-performance RAG retrieval with caching and optimization"""

    def __init__(
        self,
        embedding_model: str = 'amazon.titan-embed-text-v2:0',
        cache_host: str = None,
        use_reranking: bool = False
    ):
        self.bedrock = boto3.client('bedrock-runtime')
        self.embedding_model = embedding_model
        self.use_reranking = use_reranking

        # Initialize cache
        if cache_host:
            self.cache = redis.Redis(hostche_host)
        else:
            self.cache = None

        self.metrics = {
            'embedding_cache_hits': 0,
            'embedding_cache_misses': 0,
            'total_retrievals': 0,
            'avg_retrieval_ms': 0
        }

    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding with caching"""
        start_time = time.perf_counter()

        # Check cache
        if self.cache:
            cache_key = f"emb:{hashlib.sha256(text.encode()).hexdigest()}"
            cached = self.cache.get(cache_key)
            if cached:
                self.metrics['embedding_cache_hits'] += 1
                return np.frombuffer(cached, dtype=np.float32)
            self.metrics['embedding_cache_misses'] += 1

        # Generate embedding
        response = self.bedrock.invoke_model(
            modelId=self.embedding_model,
            body='{"inputText": "' + text.replace('"', '\\"') + '"}'
        )
        result = eval(response['body'].read())
        embedding = np.array(result['embedding'], dtype=np.float32)

        # Cache embedding
        if self.cache:
            self.cache.setex(cache_key, 3600, embedding.tobytes())

        elapsed = (time.perf_counter() - start_time) * 1000
        return embedding

    def parallel_embedding(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings in parallel"""
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.get_embedding, t): i for i, t in enumerate(texts)}
            results = [None] * len(texts)
            for future in as_completed(futures):
                idx = futures[future]
                results[idx] = future.result()
        return results

    def vector_search(
        self,
        query_embedding: np.ndarray,
        document_embeddings: List[np.ndarray],
        document_contents: List[str],
        k: int = 5,
        metadata_filter: Optional[Dict] = None
    ) -> List[Tuple[str, float]]:
        """
        Perform vector similarity search.
        In production, use OpenSearch, pgvector, or similar.
        """
        # Apply metadata filtering first (reduces search space)
        if metadata_filter:
            # Filter documents based on metadata
            # This is a simplified example
            pass

        # Calculate similarities
        scores = []
        for i, doc_emb in enumerate(document_embeddings):
            similarity = np.dot(query_embedding, doc_emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_emb)
            )
            scores.append((document_contents[i], similarity, i))

        # Sort by similarity descending
        scores.sort(key=lambda x: x[1], reverse=True)

        return [(content, score) for content, score, _ in scores[:k]]

    def hybrid_search(
        self,
        query: str,
        query_embedding: np.ndarray,
        documents: List[Dict],
        k: int = 5,
        semantic_weight: float = 0.7
    ) -> List[Tuple[str, float]]:
        """
        Combine semantic and keyword search.
        """
        # Semantic search
        doc_embeddings = [d['embedding'] for d in documents]
        doc_contents = [d['content'] for d in documents]
        semantic_results = self.vector_search(
            query_embedding, doc_embeddings, doc_contents, k=k*2
        )

        # Simple keyword search (BM25-like scoring)
        query_terms = set(query.lower().split())
        keyword_scores = []
        for doc in documents:
            doc_terms = set(doc['content'].lower().split())
            overlap = len(query_terms & doc_terms) / len(query_terms) if query_terms else 0
            keyword_scores.append((doc['content'], overlap))

        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        keyword_results = keyword_scores[:k*2]

        # Reciprocal Rank Fusion
        combined_scores = {}
        k_constant = 60  # RRF constant

        for rank, (content, _) in enumerate(semantic_results):
            if content not in combined_scores:
                combined_scores[content] = 0
            combined_scores[content] += semantic_weight / (rank + k_constant)

        for rank, (content, _) in enumerate(keyword_results):
            if content not in combined_scores:
                combined_scores[content] = 0
            combined_scores[content] += (1 - semantic_weight) / (rank + k_constant)

        # Sort by combined score
        results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        return results[:k]

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[str, float]],
        top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Rerank candidates using cross-encoder scoring.
        Simulated here - use Cohere Rerank or similar in production.
        """
        if not self.use_reranking:
            return candidates[:top_n]

        # In production, call reranking API
        # reranked = cohere_client.rerank(query, [c[0] for c in candidates])

        # Simulated reranking (in reality, use actual reranker)
        # This would typically use a cross-encoder model
        return candidates[:top_n]

    def retrieve(
        self,
        query: str,
        documents: List[Dict],
        k: int = 5,
        use_hybrid: bool = True
    ) -> Dict:
        """
        Complete retrieval pipeline with metrics.
        """
        start_time = time.perf_counter()
        self.metrics['total_retrievals'] += 1

        # 1. Generate query embedding
        embed_start = time.perf_counter()
        query_embedding = self.get_embedding(query)
        embed_time = (time.perf_counter() - embed_start) * 1000

        # 2. Search
        search_start = time.perf_counter()
        if use_hybrid:
            results = self.hybrid_search(
                query, query_embedding, documents, k=k*2
            )
        else:
            doc_embeddings = [d['embedding'] for d in documents]
            doc_contents = [d['content'] for d in documents]
            results = self.vector_search(
                query_embedding, doc_embeddings, doc_contents, k=k*2
            )
        search_time = (time.perf_counter() - search_start) * 1000

        # 3. Rerank
        rerank_start = time.perf_counter()
        final_results = self.rerank(query, results, top_n=k)
        rerank_time = (time.perf_counter() - rerank_start) * 1000

        total_time = (time.perf_counter() - start_time) * 1000
        self.metrics['avg_retrieval_ms'] = (
            self.metrics['avg_retrieval_ms'] * (self.metrics['total_retrievals'] - 1) +
            total_time
        ) / self.metrics['total_retrievals']

        return {
            'results': [{'content': c, 'score': s} for c, s in final_results],
            'metrics': {
                'embedding_ms': embed_time,
                'search_ms': search_time,
                'rerank_ms': rerank_time,
                'total_ms': total_time
            }
        }


class BedrockKnowledgeBaseRetrieval:
    """Use Bedrock Knowledge Bases for managed RAG retrieval"""

    def __init__(self, knowledge_base_id: str):
        self.bedrock_agent = boto3.client('bedrock-agent-runtime')
        self.knowledge_base_id = knowledge_base_id

    def retrieve(
        self,
        query: str,
        num_results: int = 5,
        metadata_filter: Optional[Dict] = None
    ) -> Dict:
        """Retrieve from Bedrock Knowledge Base"""
        start_time = time.perf_counter()

        params = {
            'knowledgeBaseId': self.knowledge_base_id,
            'retrievalQuery': {'text': query},
            'retrievalConfiguration': {
                'vectorSearchConfiguration': {
                    'numberOfResults': num_results
                }
            }
        }

        if metadata_filter:
            params['retrievalConfiguration']['vectorSearchConfiguration']['filter'] = metadata_filter

        response = self.bedrock_agent.retrieve(**params)

        elapsed = (time.perf_counter() - start_time) * 1000

        results = []
        for result in response.get('retrievalResults', []):
            results.append({
                'content': result['content']['text'],
                'score': result.get('score', 0),
                'source': result.get('location', {}).get('s3Location', {}).get('uri', '')
            })

        return {
            'results': results,
            'metrics': {
                'total_ms': elapsed
            }
        }


# Example usage
retrieval = OptimizedRAGRetrieval(
    cache_host='localhost',
    use_reranking=True
)

# Sample documents (in production, these would be in vector DB)
documents = [
    {
        'content': 'Amazon Bedrock is a fully managed service for foundation models.',
        'embedding': retrieval.get_embedding('Amazon Bedrock is a fully managed service.')
    },
    {
        'content': 'Lambda functions can invoke Bedrock for serverless GenAI.',
        'embedding': retrieval.get_embedding('Lambda functions for serverless GenAI.')
    }
]

# Retrieve
result = retrieval.retrieve(
    query='How to use Bedrock?',
    documents=documents,
    k=2,
    use_hybrid=True
)

print(f"Retrieval completed in {result['metrics']['total_ms']:.0f}ms")
for r in result['results']:
    print(f"  Score {r['score']:.3f}: {r['content'][:50]}...")