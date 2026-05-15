# OpenSearch mapping with metadata fields
index_mapping = {
    "mappings": {
        "properties": {
            "embedding": {
                "type": "knn_vector",
                "dimension": 1024,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "lucene"
                }
            },
            "text": {"type": "text"},
            "metadata": {
                "properties": {
                    "source": {"type": "keyword"},
                    "category": {"type": "keyword"},
                    "department": {"type": "keyword"},
                    "created_date": {"type": "date"},
                    "version": {"type": "float"},
                    "is_current": {"type": "boolean"},
                    "tags": {"type": "keyword"}  # Array of keywords
                }
            }
        }
    }
}

# Filtered vector search in OpenSearch
filtered_query = {
    "size": 5,
    "query": {
        "bool": {
            "must": [
                {
                    "knn": {
                        "embedding": {
                            "vector": query_embedding,
                            "k": 10
                        }
                    }
                }
            ],
            "filter": [
                {"term": {"metadata.category": "policy"}},
                {"term": {"metadata.is_current": True}},
                {"range": {"metadata.created_date": {"gte": "2024-01-01"}}}
            ]
        }
    }
}