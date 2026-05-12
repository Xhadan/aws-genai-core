# Search with metadata filtering
filtered_search = {
    "size": 5,
    "query": {
        "bool": {
            "must": [
                {
                    "knn": {
                        "embedding": {
                            "vector": query_embedding,
                            "k": 10  # Retrieve more for filtering
                        }
                    }
                }
            ],
            "filter": [
                {"term": {"metadata.category": "ai-ml"}},
                {"range": {"metadata.date": {"gte": "2024-01-01"}}}
            ]
        }
    }
}

results = client.search(index='rag-vectors', body=filtered_search)