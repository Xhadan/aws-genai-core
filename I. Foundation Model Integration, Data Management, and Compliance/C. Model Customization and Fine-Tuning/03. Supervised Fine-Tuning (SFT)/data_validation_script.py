import json

def validate_jsonl(filepath, required_fields=['prompt', 'completion']):
    errors = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            try:
                record = json.loads(line.strip())
                for field in required_fields:
                    if field not in record:
                        errors.append(f"Line {i}: Missing '{field}' field")
                    elif not record[field].strip():
                        errors.append(f"Line {i}: Empty '{field}' field")
            except json.JSONDecodeError as e:
                errors.append(f"Line {i}: Invalid JSON - {e}")
    return errors

# Usage
errors = validate_jsonl('training.jsonl')
if errors:
    for error in errors:
        print(error)
else:
    print("Dataset is valid!")