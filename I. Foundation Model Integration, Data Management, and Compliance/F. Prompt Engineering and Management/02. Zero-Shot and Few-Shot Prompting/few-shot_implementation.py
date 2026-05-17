import boto3

bedrock = boto3.client('bedrock-runtime')

def few_shot_classify(text, examples, categories):
    """Perform few-shot classification with examples."""

    # Build examples section
    examples_text = ""
    for ex in examples:
        examples_text += f"""Text: "{ex['text']}"
Category: {ex['category']}

"""

    prompt = f"""Classify texts into one of these categories: {', '.join(categories)}

{examples_text}Text: "{text}"
Category:"""

    response = bedrock.converse(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 50, "temperature": 0}
    )

    return response['output']['message']['content'][0]['text'].strip()


def few_shot_structured_output(text, examples, output_fields):
    """Few-shot prompting for structured output generation."""

    # Build examples
    examples_text = ""
    for i, ex in enumerate(examples, 1):
        examples_text += f"Example {i}:\nInput: {ex['input']}\nOutput:\n"
        for field, value in ex['output'].items():
            examples_text += f"  {field}: {value}\n"
        examples_text += "\n"

    # Build output template
    output_template = "\n".join([f"  {field}: [value]" for field in output_fields])

    prompt = f"""Transform the input into the structured output format shown in the examples.

{examples_text}Now process this input:
Input: {text}
Output:
{output_template}"""

    response = bedrock.converse(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 500, "temperature": 0}
    )

    return response['output']['message']['content'][0]['text']


# Few-shot classification example
examples = [
    {"text": "How do I reset my password?", "category": "Account"},
    {"text": "My Lambda function is timing out", "category": "Technical"},
    {"text": "I was charged twice this month", "category": "Billing"},
    {"text": "Can I get a demo of the product?", "category": "Sales"}
]

result = few_shot_classify(
    "I can't access my S3 bucket, getting permission denied",
    examples,
    ["Account", "Technical", "Billing", "Sales"]
)
print(f"Classification: {result}")

# Few-shot structured output
structured_examples = [
    {
        "input": "AWS Lambda is a serverless compute service that runs code in response to events",
        "output": {
            "Service": "AWS Lambda",
            "Category": "Compute",
            "Type": "Serverless",
            "Key Feature": "Event-driven code execution"
        }
    },
    {
        "input": "Amazon S3 provides object storage with high durability and availability",
        "output": {
            "Service": "Amazon S3",
            "Category": "Storage",
            "Type": "Object Storage",
            "Key Feature": "High durability (99.999999999%)"
        }
    }
]

structured_result = few_shot_structured_output(
    "Amazon DynamoDB is a fully managed NoSQL database that delivers single-digit millisecond performance",
    structured_examples,
    ["Service", "Category", "Type", "Key Feature"]
)
print(f"Structured output:\n{structured_result}")