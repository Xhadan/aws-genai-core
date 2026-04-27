import boto3

bedrock = boto3.client('bedrock')

# Purchase provisioned throughput for custom model
response = bedrock.create_provisioned_model_throughput(
    provisionedModelName='my-custom-model-pt',
    modelId='arn:aws:bedrock:us-east-1:123456789012:custom-model/my-fine-tuned-claude',
    modelUnits=1,
    commitmentDuration='OneMonth',  # or 'SixMonths' or no commitment
    tags=[
        {'key': 'Project', 'value': 'CustomerSupport'},
        {'key': 'Environment', 'value': 'Production'}
    ]
)

provisioned_arn = response['provisionedModelArn']

# Use provisioned throughput in invocation
response = bedrock.invoke_model(
    modelId=provisioned_arn,
    body=json.dumps({
        'prompt': 'Your prompt here',
        'max_tokens': 1024
    })
)