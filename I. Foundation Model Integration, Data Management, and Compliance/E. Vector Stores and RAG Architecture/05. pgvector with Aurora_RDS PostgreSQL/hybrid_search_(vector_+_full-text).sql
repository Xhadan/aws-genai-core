-- Add full-text search index
ALTER TABLE document_chunks ADD COLUMN content_tsv tsvector;
UPDATE document_chunks SET content_tsv = to_tsvector('english', content);
CREATE INDEX ON document_chunks USING gin(content_tsv);

-- Hybrid search combining vector similarity and keyword matching
WITH vector_results AS (
    SELECT
        id,
        content,
        1 - (embedding <=> $1::vector) AS vector_score
    FROM document_chunks
    ORDER BY embedding <=> $1::vector
    LIMIT 20
),
text_results AS (
    SELECT
        id,
        content,
        ts_rank(content_tsv, plainto_tsquery('english', $2)) AS text_score
    FROM document_chunks
    WHERE content_tsv @@ plainto_tsquery('english', $2)
)
SELECT
    COALESCE(v.id, t.id) AS id,
    COALESCE(v.content, t.content) AS content,
    COALESCE(v.vector_score, 0) * 0.7 +
    COALESCE(t.text_score, 0) * 0.3 AS combined_score
FROM vector_results v
FULL OUTER JOIN text_results t ON v.id = t.id
ORDER BY combined_score DESC
LIMIT 5;