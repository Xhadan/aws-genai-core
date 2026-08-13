import hashlib
def get_variant(user_id):
    hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
    return 'A' if hash_val % 100 < 50 else 'B'