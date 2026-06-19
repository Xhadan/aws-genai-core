import boto3
import json

bedrock = boto3.client('bedrock')
bedrock_runtime = boto3.client('bedrock-runtime')

def create_cross_region_profile(
    profile_name: str,
    model_id: str,
    regions: list
):
    """
    Create a cross-region inference profile for automatic failover.
    Note: This is a conceptual example - actual API may vary.
    """
    # List available inference profiles
    response = bedrock.list_inference_profiles()

    for profile in response.get('inferenceProfileSummaries', []):
        print(f"Profile: {profile['inferenceProfileName']}")
        print(f"  ARN: {profile['inferenceProfileArn']}")
        print(f"  Models: {profile.get('models', [])}")

    return response

def invoke_with_inference_profile(
    inference_profile_arn: str,
    prompt: str,
    max_tokens: int = 1024
):
    """
    Invoke model using inference profile for cross-region routing.
    """
    response = bedrock_runtime.invoke_model(
        modelId=inference_profile_arn,  # Use profile ARN
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        })
    )

    result = json.loads(response['body'].read())
    return result['content'][0]['text']

# Example: Use system-defined cross-region profile
# These provide automatic routing across supported regions
profile_arn = "arn:aws:bedrock:us:anthropic.claude-3-sonnet-20240229-v1:0"
response = invoke_with_inference_profile(profile_arn, "Hello!")