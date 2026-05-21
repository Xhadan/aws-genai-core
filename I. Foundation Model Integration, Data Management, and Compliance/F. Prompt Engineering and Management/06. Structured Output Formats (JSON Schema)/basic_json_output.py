import boto3
import json

bedrock = boto3.client('bedrock-runtime')

def request_json_output(prompt, schema_description):
    """Request JSON output with explicit schema."""

    full_prompt = f"""{prompt}

Respond with a JSON object following this exact structure:
{schema_description}

Important:
- Return ONLY valid JSON
- No markdown code blocks
- No explanatory text before or after
- All specified fields must be present"""

    response = bedrock.converse(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        messages=[{"role": "user", "content": [{"text": full_prompt}]}],
        inferenceConfig={
            "maxTokens": 1024,
            "temperature": 0  # Lower temperature for consistent structure
        }
    )

    text = response['output']['message']['content'][0]['text']

    # Parse and return JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group())
        raise ValueError(f"Could not parse JSON from response: {text}")


# Example: Analyze text and return structured data
schema = """{
  "sentiment": "positive" | "negative" | "neutral",
  "confidence": number between 0.0 and 1.0,
  "key_topics": ["array", "of", "strings"],
  "summary": "one sentence summary"
}"""

result = request_json_output(
    prompt="Analyze this customer review: 'The AWS Lambda service is incredibly easy to use. The auto-scaling works perfectly. However, cold starts can be annoying for real-time applications.'",
    schema_description=schema
)

print(json.dumps(result, indent=2))
# Output:
# {
#   "sentiment": "positive",
#   "confidence": 0.75,
#   "key_topics": ["AWS Lambda", "auto-scaling", "cold starts"],
#   "summary": "Positive review of Lambda's ease of use and scaling, with minor concern about cold starts."
# }