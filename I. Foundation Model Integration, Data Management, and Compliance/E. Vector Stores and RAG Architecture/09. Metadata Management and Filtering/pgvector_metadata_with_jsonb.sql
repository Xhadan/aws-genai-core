-- Table with JSONB metadata
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1024),
    metadata JSONB NOT NULL DEFAULT '{}'
);

-- Create indexes for common metadata queries
CREATE INDEX idx_metadata_category ON document_chunks
    USING GIN ((metadata->'category'));

CREATE INDEX idx_metadata_department ON document_chunks
    USING BTREE ((metadata->>'department'));

CREATE INDEX idx_metadata_date ON document_chunks
    USING BTREE (((metadata->>'created_date')::date));

-- Query with metadata filters
SELECT content, metadata,
       1 - (embedding <=> $1::vector) AS similarity
FROM document_chunks
WHERE
    metadata->>'category' = 'policy'
    AND metadata->>'department' IN ('hr', 'legal')
    AND (metadata->>'created_date')::date >= '2024-01-01'
    AND (metadata->>'is_current')::boolean = true
ORDER BY embedding <=> $1::vector
LIMIT 5;

-- Query with JSONB containment (tags)
SELECT content
FROM document_chunks
WHERE
    metadata @> '{"tags": ["security"]}'
ORDER BY embedding <=> $1::vector
LIMIT 5;