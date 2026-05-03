import boto3

sm_client = boto3.client('sagemaker')

# Update model approval status
sm_client.update_model_package(
    ModelPackageArn='arn:aws:sagemaker:us-east-1:123456789012:model-package/genai-custom-models/2',
    ModelApprovalStatus='Approved',
    ApprovalDescription='Passed all quality gates and security review'
)

# This triggers EventBridge event for CI/CD automation