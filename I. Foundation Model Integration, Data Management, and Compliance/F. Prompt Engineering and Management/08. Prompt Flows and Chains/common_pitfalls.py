def safe_step(func):
    try:
        result = func()
        if not validate(result):
            return fallback_value
        return result
    except Exception as e:
        log_error(e)
        return fallback_value