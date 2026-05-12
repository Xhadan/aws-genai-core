-- Create table for RAG document chunks
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024),  -- Match Titan Embeddings V2 dimension
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (document_id, chunk_index)
);

-- Create HNSW index for fast similarity search
CREATE INDEX ON document_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Alternative: IVFFlat index (faster to build)
-- CREATE INDEX ON document_chunks
-- USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);  -- Rule: lists = sqrt(num_rows)