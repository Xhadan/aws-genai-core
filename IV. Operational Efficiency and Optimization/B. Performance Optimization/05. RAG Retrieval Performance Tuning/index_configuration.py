# High accuracy, moderate speed
hnsw_params = {
    "ef_construction": 256,
    "ef_search": 128,
    "m": 16
}

# Faster search, slightly lower accuracy
hnsw_params_fast = {
    "ef_construction": 128,
    "ef_search": 64,
    "m": 12
}