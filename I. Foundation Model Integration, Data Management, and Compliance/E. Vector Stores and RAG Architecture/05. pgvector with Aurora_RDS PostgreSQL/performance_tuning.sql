-- Increase work_mem for vector operations
SET work_mem = '256MB';

-- Set maintenance_work_mem for index building
SET maintenance_work_mem = '1GB';

-- HNSW index tuning
-- Increase ef_search for better recall (trade-off: slower queries)
SET hnsw.ef_search = 100;  -- Default is 40

-- IVFFlat: Increase probes for better recall
SET ivfflat.probes = 10;  -- Default is 1

-- Parallel query execution
SET max_parallel_workers_per_gather = 4;

-- Analyze table for query optimizer
ANALYZE document_chunks;