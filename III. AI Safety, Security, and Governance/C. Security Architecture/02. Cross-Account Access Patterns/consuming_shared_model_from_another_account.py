import boto3

# In consumer account
bedrock_runtime = boto3.client('bedrock-runtime')

def invoke_shared_model(provider_account_id, model_id, prompt):
    """
    Invoke a model shared from another account.
    Use the cross-account ARN format.
    """
    model_arn = f"arn:aws:bedrock:us-east-1:{provider_account_id}:custom-model/{model_id}"

    response = bedrock_runtime.converse(
        modelId=model_arn,  # Use full ARN for cross-account
        messages=[
            {"role": "user", "content": [{"text": prompt}]}
        ],
        inferenceConfig={"maxTokens": 1024}
    )

    return response['output']['message']['content'][0]['text']

# Use model from provider account
result = invoke_shared_model(
    provider_account_id='999999999999',  # Provider account
    model_id='shared-custom-model',
    prompt='Analyze this financial report.'
)
print(result)