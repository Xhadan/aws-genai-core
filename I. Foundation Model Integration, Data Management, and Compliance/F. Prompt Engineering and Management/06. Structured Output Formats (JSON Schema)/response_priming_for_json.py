import boto3
import json

bedrock = boto3.client('bedrock-runtime')

def json_with_priming(prompt, schema_hint):
    """Use response priming to ensure JSON output."""

    messages = [
        {
            "role": "user",
            "content": [{"text": f"""{prompt}

Respond with valid JSON matching this structure:
{schema_hint}"""}]
        },
        {
            "role": "assistant",
            "content": [{"text": "{"}]  # Prime with opening brace
        }
    ]

    response = bedrock.converse(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        messages=messages,
        inferenceConfig={
            "maxTokens": 1024,
            "temperature": 0
        }
    )

    # Prepend the priming brace to the response
    text = "{" + response['output']['message']['content'][0]['text']

    return json.loads(text)


# Example usage
result = json_with_priming(
    prompt="Extract entities from: 'John Smith from Acme Corp contacted us about upgrading their AWS account.'",
    schema_hint='{"person": "name", "company": "company name", "action": "what they want"}'
)

print(json.dumps(result, indent=2))