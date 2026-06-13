import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime')

def invoke_with_provisioned_throughput(
    prompt: str,
    provisioned_model_arn: str
):
    """
    Invoke model using Provisioned Throughput.
    Uses the provisioned ARN instead of base model ID.
    """
    response = bedrock_runtime.invoke_model(
        modelId=provisioned_model_arn,  # Use provisioned ARN
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })
    )

    result = json.loads(response['body'].read())
    return result['content'][0]['text']

# Use provisioned throughput
provisioned_arn = "arn:aws:bedrock:us-east-1:123456789012:provisioned-model/abc123"
response = invoke_with_provisioned_throughput(
    prompt="Summarize the key features of our premium plan.",
    provisioned_model_arn=provisioned_arn
)
print(response)