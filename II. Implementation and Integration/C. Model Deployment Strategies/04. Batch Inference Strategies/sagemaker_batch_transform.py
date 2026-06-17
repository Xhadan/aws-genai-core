import boto3
import sagemaker
from sagemaker.transformer import Transformer

def create_batch_transform_job(
    model_name: str,
    input_s3_uri: str,
    output_s3_uri: str,
    instance_type: str = "ml.g5.2xlarge",
    instance_count: int = 2
):
    """
    Create a SageMaker Batch Transform job.
    """
    transformer = Transformer(
        model_name=model_name,
        instance_count=instance_count,
        instance_type=instance_type,
        output_path=output_s3_uri,
        assemble_with="Line",
        accept="application/json",
        strategy="MultiRecord",  # Process multiple records per request
        max_concurrent_transforms=4,
        max_payload=6  # MB
    )

    transformer.transform(
        data=input_s3_uri,
        content_type="application/json",
        split_type="Line",  # Each line is a separate record
        join_source="Input",  # Include input in output for matching
        waitlse  # Don't block
    )

    return transformer.latest_transform_job

def create_batch_transform_from_jumpstart(
    model_id: str,
    input_s3_uri: str,
    output_s3_uri: str
):
    """
    Create batch transform using JumpStart model.
    """
    from sagemaker.jumpstart.model import JumpStartModel

    model = JumpStartModel(model_id=model_id)

    transformer = model.transformer(
        instance_count=1,
        instance_type="ml.g5.2xlarge",
        output_path=output_s3_uri,
        strategy="SingleRecord"
    )

    transformer.transform(
        data=input_s3_uri,
        content_type="application/json",
        split_type="Line",
        wait=True
    )

    return transformer.latest_transform_job

# Prepare input data
input_data = [
    {"inputs": "Summarize: Cloud computing enables..."},
    {"inputs": "Summarize: Machine learning models..."},
    {"inputs": "Summarize: Serverless architecture..."}
]

# Upload to S3
s3 = boto3.client('s3')
for idx, record in enumerate(input_data):
    s3.put_object(
        Bucket="my-batch-bucket",
        Key=f"transform-input/record-{idx}.json",
        Body=json.dumps(record)
    )

# Run transform
job = create_batch_transform_job(
    model_name="my-llm-model",
    input_s3_uri="s3://my-batch-bucket/transform-input/",
    output_s3_uri="s3://my-batch-bucket/transform-output/"
)