import hashlib

def generate_cache_key(prompt, model_id, params):
    """Generate deterministic cache key"""
    key_string = f"{model_id}:{prompt}:{json.dumps(params, sort_keys=True)}"
    return hashlib.sha256(key_string.encode()).hexdigest()