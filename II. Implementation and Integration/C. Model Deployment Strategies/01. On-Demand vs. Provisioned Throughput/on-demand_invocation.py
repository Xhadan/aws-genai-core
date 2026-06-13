import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime')

def invoke_model_on_demand(prompt: str, model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"):
    """
    Invoke model using On-Demand pricing.
    Charges apply per token processed.
    """
    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })
    )

    result = json.loads(response['body'].read())

    # Extract usage for cost tracking
    usage = result.get('usage', {})
    input_tokens = usage.get('input_tokens', 0)
    output_tokens = usage.get('output_tokens', 0)

    print(f"Input tokens: {input_tokens}, Output tokens: {output_tokens}")

    return result['content'][0]['text']

# Example usage
response = invoke_model_on_demand("Explain quantum computing in one paragraph.")
print(response)