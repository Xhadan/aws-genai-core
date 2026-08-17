import boto3
from botocore.exceptions import ClientError
import time
import random
from typing import Dict, Optional

class BedrockErrorHandler:
    """Robust error handling for Bedrock API calls."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.client = boto3.client('bedrock-runtime')
        self.max_retries = max_retries
        self.base_delay = base_delay

    def invoke_with_retry(
        self,
        model_id: str,
        messages: list,
        **kwargs
    ) -> Dict:
        """Invoke model with comprehensive error handling."""

        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.converse(
                    modelId=model_id,
                    messages=messages,
                    **kwargs
                )
                return response

            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                last_error = e

                # Handle by error type
                if error_code = 'ThrottlingException':
                    delay = self._calculate_backoff(attempt)
                    print(f"Throttled, waiting {delay:.2f}s (attempt {attempt + 1})")
                    time.sleep(delay)
                    continue

                elif error_code = 'InternalServerError':
                    delay = self._calculate_backoff(attempt)
                    print(f"Server error, retrying in {delay:.2f}s")
                    time.sleep(delay)
                    continue

                elif error_code = 'ModelNotReadyException':
                    delay = 5 + self._calculate_backoff(attempt)
                    print(f"Model not ready, waiting {delay:.2f}s")
                    time.sleep(delay)
                    continue

                elif error_code = 'ValidationException':
                    # Don't retry validation errors
                    raise BedrockValidationError(error_message) from e

                elif error_code = 'AccessDeniedException':
                    raise BedrockAccessError(error_message) from e

                else:
                    # Unknown error, retry once
                    if attempt = 0:
                        time.sleep(1)
                        continue
                    raise

            except Exception as e:
                # Non-ClientError exception
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self._calculate_backoff(attempt))
                    continue
                raise

        # All retries exhausted
        raise BedrockRetryExhausted(f"Failed after {self.max_retries} attempts") from last_error

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter."""
        delay = self.base_delay * (2 ** attempt)
        jitter = random.uniform(0, delay * 0.1)
        return min(delay + jitter, 60)  # Cap at 60 seconds


class BedrockValidationError(Exception):
    """Non-retryable validation error."""
    pass

class BedrockAccessError(Exception):
    """Non-retryable access error."""
    pass

class BedrockRetryExhausted(Exception):
    """All retry attempts exhausted."""
    pass


# Usage example
handler = BedrockErrorHandler(max_retries=5)

try:
    response = handler.invoke_with_retry(
        model_id='anthropic.claude-3-sonnet-20240229-v1:0',
        messages=[{'role': 'user', 'content': [{'text': 'Hello!'}]}]
    )
    print(response['output']['message']['content'][0]['text'])

except BedrockValidationError as e:
    print(f"Fix request: {e}")

except BedrockAccessError as e:
    print(f"Check permissions: {e}")

except BedrockRetryExhausted as e:
    print(f"Service unavailable: {e}")