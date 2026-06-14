import boto3
from sagemaker.async_inference import AsyncInferenceConfig
from sagemaker.huggingface import HuggingFaceModel

def deploy_async_endpoint(
    model_data: str,
    endpoint_name: str = "llm-async-endpoint",
    output_bucket: str = "my-async-results"
):
    """
    Deploy an asynchronous inference endpoint for batch processing.
    """
    # Configure async inference
    async_config = AsyncInferenceConfig(
        output_path=f"s3://{output_bucket}/async-results/",
        max_concurrent_invocations_per_instance=4,
        notification_config={
            "SuccessTopic": "arn:aws:sns:us-east-1:123456789012:async-success",
            "ErrorTopic": "arn:aws:sns:us-east-1:123456789012:async-error"
        }
    )

    model = HuggingFaceModel(
        model_data=model_data,
        role=sagemaker.get_execution_role(),
        transformers_version="4.37.0",
        pytorch_version="2.1.0",
        py_version="py310"
    )

    predictor = model.deploy(
        initial_instance_count=1,
        instance_type="ml.g5.2xlarge",
        endpoint_name=endpoint_name,
        async_inference_config=async_config
    )

    return predictor

def invoke_async_endpoint(endpoint_name: str, input_s3_uri: str):
    """Submit async inference request."""
    runtime = boto3.client('sagemaker-runtime')

    response = runtime.invoke_endpoint_async(
        EndpointName=endpoint_name,
        InputLocation=input_s3_uri,
        ContentType="application/json",
        Accept="application/json"
    )

    output_location = response['OutputLocation']
    return output_location

def poll_async_result(output_location: str, timeout: int = 3600):
    """Poll for async inference result."""
    import time

    s3 = boto3.client('s3')
    bucket, key = output_location.replace("s3://", "").split("/", 1)

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            return json.loads(response['Body'].read().decode())
        except s3.exceptions.NoSuchKey:
            time.sleep(10)  # Wait and retry

    raise TimeoutError("Async inference did not complete in time")