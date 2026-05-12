-- Connect to your Aurora/RDS PostgreSQL database
-- Enable the pgvector extension (requires rds_superuser role)
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT extversion FROM pg_extension WHERE extname = 'vector';
-- Returns: 0.5.1 (or current version)