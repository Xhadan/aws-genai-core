import boto3

bedrock = boto3.client('bedrock-runtime')

def zero_shot_classify(text, categories):
    """Perform zero-shot classification without examples."""

    prompt = f"""Classify the following text into exactly one of these categories: {', '.join(categories)}

Text: "{text}"

Respond with only the category name, nothing else.

Category:"""

    response = bedrock.converse(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 50, "temperature": 0}
    )

    return response['output']['message']['content'][0]['text'].strip()


def zero_shot_extract(text, fields):
    """Zero-shot information extraction."""

    fields_list = '\n'.join([f"- {field}" for field in fields])

    prompt = f"""Extract the following information from the text below.
If a field is not found, use "Not specified".

Fields to extract:
{fields_list}

Text: "{text}"

Respond in this exact format:
{chr(10).join([f'{field}: [extracted value]' for field in fields])}"""

    response = bedrock.converse(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 500, "temperature": 0}
    )

    return response['output']['message']['content'][0]['text']


# Examples
sentiment = zero_shot_classify(
    "The new AWS feature is amazing but documentation could be better",
    ["Positive", "Negative", "Mixed", "Neutral"]
)
print(f"Sentiment: {sentiment}")

# Information extraction
info = zero_shot_extract(
    "Please contact John Smith at john@example.com or call 555-123-4567 regarding the Enterprise account renewal for Acme Corp.",
    ["Name", "Email", "Phone", "Company", "Topic"]
)
print(f"Extracted info:\n{info}")