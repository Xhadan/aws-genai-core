def search_similar(query, top_k=5, threshold=0.7):
    """Search for similar document chunks."""
    query_embedding = get_embedding(query)

    # Cosine similarity search (using cosine distance)
    cursor.execute("""
        SELECT
            document_id,
            chunk_index,
            content,
            metadata,
            1 - (embedding <=> %s::vector) AS similarity
        FROM document_chunks
        WHERE 1 - (embedding <=> %s::vector) > %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, (query_embedding, query_embedding, threshold, query_embedding, top_k))

    results = []
    for row in cursor.fetchall():
        results.append({
            'document_id': row[0],
            'chunk_index': row[1],
            'content': row[2],
            'metadata': row[3],
            'similarity': float(row[4])
        })

    return results

# Search example
results = search_similar("What foundation models does Bedrock support?")
for r in results:
    print(f"[{r['similarity']:.3f}] {r['content'][:100]}...")