import boto3
from sagemaker import ModelPackage

sm_client = boto3.client('sagemaker')

# Create Model Package Group (one-time)
sm_client.create_model_package_group(
    ModelPackageGroupName='genai-custom-models',
    ModelPackageGroupDescription='Fine-tuned foundation models for GenAI apps'
)

# Register a new model version
model_package_input = {
    'ModelPackageGroupName': 'genai-custom-models',
    'ModelPackageDescription': 'Llama-2 fine-tuned for customer support',
    'InferenceSpecification': {
        'Containers': [{
            'Image': '763104351884.dkr.ecr.us-east-1.amazonaws.com/huggingface-pytorch-inference:2.1.0-transformers4.36.0-gpu-py310-cu121-ubuntu22.04',
            'ModelDataUrl': 's3://my-bucket/models/llama-support-v1/model.tar.gz',
            'Environment': {
                'HF_MODEL_ID': '/opt/ml/model',
                'SM_NUM_GPUS': '1'
            }
        }],
        'SupportedTransformInstanceTypes': ['ml.g5.xlarge'],
        'SupportedRealtimeInferenceInstanceTypes': ['ml.g5.xlarge'],
        'SupportedContentTypes': ['application/json'],
        'SupportedResponseMIMETypes': ['application/json']
    },
    'ModelApprovalStatus': 'PendingManualApproval',
    'ModelMetrics': {
        'ModelQuality': {
            'Statistics': {
                'ContentType': 'application/json',
                'S3Uri': 's3://my-bucket/metrics/quality-metrics.json'
            }
        }
    },
    'MetadataProperties': {
        'TrainingJobArn': 'arn:aws:sagemaker:us-east-1:123456789012:training-job/llama-ft-2025',
        'BaseModelId': 'meta-llama/Llama-2-7b-hf',
        'FineTuningMethod': 'LoRA',
        'LoraRank': '16'
    }
}

response = sm_client.create_model_package(**model_package_input)
print(f"Model Package ARN: {response['ModelPackageArn']}")