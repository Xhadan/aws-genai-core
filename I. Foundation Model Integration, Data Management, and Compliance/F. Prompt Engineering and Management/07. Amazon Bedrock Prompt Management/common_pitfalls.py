def validate_variables(prompt_variables, required_vars):
    missing = [v for v in required_vars if v not in prompt_variables]
    if missing:
        raise ValueError(f"Missing required variables: {missing}")