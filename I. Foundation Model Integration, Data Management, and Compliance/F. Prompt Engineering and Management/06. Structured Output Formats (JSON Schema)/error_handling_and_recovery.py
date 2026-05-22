import boto3
import json
import re
from typing import TypeVar, Type, Optional
from pydantic import BaseModel

bedrock = boto3.client('bedrock-runtime')

T = TypeVar('T', boundseModel)

class JSONExtractionError(Exception):
    """Custom exception for JSON extraction failures."""
    pass

def extract_json_robust(text: str) -> dict:
    """Extract JSON from text with multiple fallback strategies."""

    strategies = [
        # Strategy 1: Direct parse
        lambda t: json.loads(t),

        # Strategy 2: Extract from markdown code block
        lambda t: json.loads(re.search(r'```(?:json)?\s*([\s\S]*?)```', t).group(1)),

        # Strategy 3: Find JSON object pattern
        lambda t: json.loads(re.search(r'\{[\s\S]*\}', t).group()),

        # Strategy 4: Find JSON array pattern
        lambda t: json.loads(re.search(r'\[[\s\S]*\]', t).group()),

        # Strategy 5: Try fixing common issues
        lambda t: json.loads(
            t.replace("'", '"')  # Single to double quotes
             .replace('True', 'true')
             .replace('False', 'false')
             .replace('None', 'null')
        ),
    ]

    for strategy in strategies:
        try:
            return strategy(text)
        except (json.JSONDecodeError, AttributeError, TypeError):
            continue

    raise JSONExtractionError(f"Could not extract valid JSON from: {text[:200]}...")


def get_json_with_retry(
    prompt: str,
    schema_class: Type[T],
    max_retries: int = 3,
    model_id: str = 'anthropic.claude-3-5-sonnet-20241022-v2:0'
) -> Optional[T]:
    """Get validated JSON with automatic retry on failure."""

    schema = schema_class.model_json_schema()
    errors = []

    for attempt in range(max_retries):
        error_context = ""
        if errors:
            error_context = f"\n\nPrevious attempts failed with these errors:\n" + \
                          "\n".join(f"- {e}" for e in errors[-2:])  # Last 2 errors

        full_prompt = f"""{prompt}

Respond with a JSON object matching this schema:
{json.dumps(schema, indent=2)}

CRITICAL: Return ONLY valid JSON. No text before or after.{error_context}"""

        try:
            response = bedrock.converse(
                modelId=model_id,
                messages=[{"role": "user", "content": [{"text": full_prompt}]}],
                inferenceConfig={"maxTokens": 2048, "temperature": 0.1 * attempt}  # Increase temp on retry
            )

            text = response['output']['message']['content'][0]['text']
            data = extract_json_robust(text)
            return schema_class.model_validate(data)

        except JSONExtractionError as e:
            errors.append(f"JSON extraction failed: {str(e)}")
        except Exception as e:
            errors.append(f"Validation failed: {str(e)}")

    # All retries exhausted
    raise ValueError(f"Failed after {max_retries} attempts. Errors: {errors}")


# Example usage with error handling
class SimpleAnalysis(BaseModel):
    category: str
    score: float
    tags: list[str]

try:
    result = get_json_with_retry(
        prompt="Analyze: 'AWS Lambda reduces operational overhead'",
        schema_class=SimpleAnalysis,
        max_retries=3
    )
    print(f"Result: {result}")
except ValueError as e:
    print(f"Failed to get valid response: {e}")
    # Implement fallback logic