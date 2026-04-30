import boto3

bedrock = boto3.client('bedrock-runtime')

# Method 1: Use system-defined cross-region profile
response = bedrock.converse(
    # US geographic profile - routes within US regions
    modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
    messages=[
        {'role': 'user', 'content': [{'text': 'Hello!'}]}
    ]
)

# Method 2: Use global profile for maximum throughput
response = bedrock.converse(
    # Global profile - routes to any region
    modelId='global.anthropic.claude-sonnet-4-5-20250929-v1:0',
    messages=[
        {'role': 'user', 'content': [{'text': 'Complex analysis...'}]}
    ]
)

# Method 3: Use application profile for cost tracking
response = bedrock.converse(
    # Custom application profile ARN
    modelId='arn:aws:bedrock:us-east-1:123456789012:inference-profile/my-app-profile',
    messages=[
        {'role': 'user', 'content': [{'text': 'Track my costs'}]}
    ]
)

# No significant code changes needed - just use profile ID/ARN!