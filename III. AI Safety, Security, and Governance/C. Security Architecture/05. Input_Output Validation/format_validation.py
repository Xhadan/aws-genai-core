def validate_input_format(data):
    required = ['prompt', 'session_id']
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    if not isinstance(data['prompt'], str):
        raise TypeError("Prompt must be string")