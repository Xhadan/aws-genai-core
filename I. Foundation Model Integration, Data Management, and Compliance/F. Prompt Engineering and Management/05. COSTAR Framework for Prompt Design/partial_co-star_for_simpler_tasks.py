import boto3

bedrock = boto3.client('bedrock-runtime')

def quick_costar(objective: str,
                 context: str = None,
                 response_format: str = None,
                 audience: str = None):
    """
    Simplified CO-STAR for quick tasks.
    Uses only the most essential components.
    """

    prompt_parts = []

    if context:
        prompt_parts.append(f"Context: {context}")

    prompt_parts.append(f"Task: {objective}")

    if audience:
        prompt_parts.append(f"Audience: {audience}")

    if response_format:
        prompt_parts.append(f"Format: {response_format}")

    prompt = "\n\n".join(prompt_parts)

    response = bedrock.converse(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 1024, "temperature": 0.7}
    )

    return response['output']['message']['content'][0]['text']


# Example: Quick task with minimal CO-STAR
result = quick_costar(
    objective="Explain the difference between AWS Lambda and EC2 for running scheduled jobs",
    audience="Developer new to AWS serverless",
    response_format="Comparison table followed by recommendation paragraph"
)

print(result)

# Example: Full context but simple format
result2 = quick_costar(
    context="Company uses Lambda for API endpoints but EC2 for batch processing. Considering consolidation.",
    objective="Recommend whether to keep the hybrid approach or consolidate",
    response_format="3-4 bullet points with clear recommendation"
)

print(result2)