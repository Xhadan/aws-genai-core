import random

def select_prompt_version(user_id, test_config):
    # Consistent assignment based on user
    bucket = hash(user_id) % 100

    if bucket < test_config['version_a_percentage']:
        return 'version_a'
    else:
        return 'version_b'