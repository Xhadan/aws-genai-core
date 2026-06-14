from sagemaker.jumpstart.model import JumpStartModel

def deploy_jumpstart_fm(
    model_id: str = "meta-textgeneration-llama-3-1-8b-instruct",
    instance_type: str = "ml.g5.2xlarge",
    endpoint_name: str = "jumpstart-llama3-endpoint"
):
    """
    Deploy a foundation model from SageMaker JumpStart.
    """
    model = JumpStartModel(
        model_id=model_id,
        instance_type=instance_type,
        env={
            "MAX_INPUT_LENGTH": "4096",
            "MAX_TOTAL_TOKENS": "8192",
            "MAX_BATCH_TOTAL_TOKENS": "16384"
        }
    )

    predictor = model.deploy(
        initial_instance_count=1,
        endpoint_name=endpoint_name,
        accept_eula=True  # Required for gated models
    )

    return predictor

def query_jumpstart_llm(predictor, prompt: str):
    """Query the deployed JumpStart LLM."""
    payload = {
        "inputs": [
            [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        ],
        "parameters": {
            "max_new_tokens": 512,
            "top_p": 0.9,
            "temperature": 0.6
        }
    }

    response = predictor.predict(payload)
    return response[0]["generation"]["content"]

# Deploy and use
predictor = deploy_jumpstart_fm()
response = query_jumpstart_llm(predictor, "Explain machine learning in simple terms.")
print(response)