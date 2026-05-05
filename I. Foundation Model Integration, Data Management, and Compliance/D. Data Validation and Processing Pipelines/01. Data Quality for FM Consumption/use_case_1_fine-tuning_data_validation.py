import json
from collections import Counter

def validate_training_data(filepath):
    issues = []
    seen_prompts = set()

    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            try:
                record = json.loads(line)

                # Completeness
                if 'prompt' not in record or not record['prompt'].strip():
                    issues.append(f"Line {i}: Missing or empty prompt")
                if 'completion' not in record or not record['completion'].strip():
                    issues.append(f"Line {i}: Missing or empty completion")

                # Length validation (assuming 4096 token limit ~16K chars)
                if len(record.get('prompt', '')) > 16000:
                    issues.append(f"Line {i}: Prompt too long")
                if len(record.get('completion', '')) > 8000:
                    issues.append(f"Line {i}: Completion too long")

                # Uniqueness
                prompt_hash = hash(record.get('prompt', ''))
                if prompt_hash in seen_prompts:
                    issues.append(f"Line {i}: Duplicate prompt")
                seen_prompts.add(prompt_hash)

            except json.JSONDecodeError:
                issues.append(f"Line {i}: Invalid JSON")

    return issues