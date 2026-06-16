from sagemaker.serverless import ServerlessInferenceConfig
from sagemaker.huggingface import HuggingFaceModel

def deploy_serverless_endpoint(
    model_data: str,
    endpoint_name: str = "llm-serverless-endpoint"
):
    """
    Deploy a serverless inference endpoint.
    Note: Serverless has memory limits, suitable for smaller models.
    """
    serverless_config = ServerlessInferenceConfig(
        memory_size_in_mba44,  # Max 6GB
        max_concurrency,
        provisioned_concurrency=0  # Set > 0 to reduce cold starts
    )

    model = HuggingFaceModel(
        model_data=model_data,
        role=sagemaker.get_execution_role(),
        transformers_version="4.37.0",
        pytorch_version="2.1.0",
        py_version="py310"
    )

    predictor = model.deploy(
        endpoint_name=endpoint_name,
        serverless_inference_config=serverless_config
    )

    return predictor

# Note: For large FMs, serverless may not be suitable due to memory limits
# Consider using smaller models like Phi-2, TinyLlama, or distilled models