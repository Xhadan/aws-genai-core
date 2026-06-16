import boto3
import sagemaker
from sagemaker.huggingface import HuggingFaceModel

sagemaker_session = sagemaker.Session()
role = sagemaker.get_execution_role()

def deploy_realtime_endpoint(
    model_data: str,
    instance_type: str = "ml.g5.2xlarge",
    endpoint_name: str = "llm-realtime-endpoint"
):
    """
    Deploy a real-time inference endpoint for an LLM.
    """
    # Define the Hugging Face model
    huggingface_model = HuggingFaceModel(
        model_data=model_data,  # S3 path to model artifacts
        role=role,
        transformers_version="4.37.0",
        pytorch_version="2.1.0",
        py_version="py310",
        env={
            "HF_MODEL_ID": "mistralai/Mistral-7B-Instruct-v0.2",
            "SM_NUM_GPUS": "1",
            "MAX_INPUT_LENGTH": "4096",
            "MAX_TOTAL_TOKENS": "8192"
        }
    )

    # Deploy to real-time endpoint
    predictor = huggingface_model.deploy(
        initial_instance_count=1,
        instance_type=instance_type,
        endpoint_name=endpoint_name,
        container_startup_health_check_timeout`0,
        model_data_download_timeout`0
    )

    return predictor

def invoke_realtime_endpoint(endpoint_name: str, prompt: str):
    """Invoke real-time endpoint for inference."""
    runtime = boto3.client('sagemaker-runtime')

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True
        }
    }

    response = runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType="application/json",
        Body=json.dumps(payload)
    )

    result = json.loads(response['Body'].read().decode())
    return result[0]['generated_text']