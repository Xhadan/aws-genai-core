-- Search with metadata filters using JSONB
SELECT
    document_id,
    content,
    metadata,
    1 - (embedding <=> $1::vector) AS similarity
FROM document_chunks
WHERE
    metadata->>'category' = 'ai-ml'
    AND metadata->>'source' = 'aws-docs'
    AND 1 - (embedding <=> $1::vector) > 0.7
ORDER BY embedding <=> $1::vector
LIMIT 5;

-- Search with date range filter
SELECT content, metadata
FROM document_chunks
WHERE
    (metadata->>'date')::date >= '2024-01-01'
    AND 1 - (embedding <=> $1::vector) > 0.6
ORDER BY embedding <=> $1::vector
LIMIT 10;