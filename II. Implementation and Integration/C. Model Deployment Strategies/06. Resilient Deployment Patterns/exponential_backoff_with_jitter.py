import random
import time
from functools import wraps

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2,
    jitter: bool = True
):
    """
    Decorator for retry with exponential backoff and jitter.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** (retries - 1)),
                        max_delay
                    )

                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    print(f"Retry {retries}/{max_retries} after {delay:.2f}s: {e}")
                    time.sleep(delay)

        return wrapper
    return decorator

@retry_with_backoff(max_retries=3, base_delay=1.0)
def invoke_with_retry(client, model_id: str, prompt: str):
    """Invoke model with automatic retry on transient failures."""
    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        })
    )
    return json.loads(response['body'].read())