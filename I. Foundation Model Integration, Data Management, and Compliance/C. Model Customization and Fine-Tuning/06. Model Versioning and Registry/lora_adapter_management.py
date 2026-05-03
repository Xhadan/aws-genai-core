# For LoRA models, register adapter separately or combined
model_package_input = {
    'ModelPackageGroupName': 'customer-support-adapters',
    'ModelPackageDescription': 'LoRA adapter for support domain',
    'MetadataProperties': {
        'BaseModel': 'meta-llama/Llama-2-7b-hf',
        'AdapterType': 'LoRA',
        'LoraRank': '16',
        'LoraAlpha': '32',
        'TargetModules': 'q_proj,k_proj,v_proj,o_proj',
        'TrainingDataVersion': 'support-data-v2.3',
        'MergedWeights': 'False'  # Adapter stored separately
    },
    'InferenceSpecification': {
        'Containers': [{
            'ModelDataUrl': 's3://my-bucket/adapters/support-lora-v2/',  # Just adapter weights
            # ... container config
        }]
    }
}