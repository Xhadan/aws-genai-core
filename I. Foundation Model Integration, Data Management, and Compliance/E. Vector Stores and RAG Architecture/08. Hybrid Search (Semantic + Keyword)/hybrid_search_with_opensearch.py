from opensearchpy import OpenSearch

client = OpenSearch(
    hosts=[{'host': 'your-cluster.us-east-1.aoss.amazonaws.com', 'port': 443}],
    use_ssl=True
)

def hybrid_search(query_text, query_embedding, alpha=0.7):
    """
    Perform hybrid search combining vector and BM25.
    alpha: weight for vector search (0-1), keyword gets (1-alpha)
    """

    # Hybrid query using OpenSearch neural search
    hybrid_query = {
        "size": 10,
        "query": {
            "hybrid": {
                "queries": [
                    # Vector search component
                    {
                        "neural": {
                            "embedding": {
                                "query_text": query_text,
                                "k": 20
                            }
                        }
                    },
                    # BM25 keyword search component
                    {
                        "match": {
                            "text": {
                                "query": query_text
                            }
                        }
                    }
                ]
            }
        },
        # Score normalization and combination
        "search_pipeline": {
            "phase_results_processors": [
                {
                    "normalization-processor": {
                        "normalization": {
                            "technique": "min_max"
                        },
                        "combination": {
                            "technique": "arithmetic_mean",
                            "parameters": {
                                "weights": [alpha, 1 - alpha]
                            }
                        }
                    }
                }
            ]
        }
    }

    results = client.search(index='rag-index', body=hybrid_query)
    return results['hits']['hits']

# Example: More weight on vector search
results = hybrid_search(
    query_text="How to configure IAM roles for Lambda?",
    query_embedding=get_embedding("How to configure IAM roles for Lambda?"),
    alpha=0.7
)