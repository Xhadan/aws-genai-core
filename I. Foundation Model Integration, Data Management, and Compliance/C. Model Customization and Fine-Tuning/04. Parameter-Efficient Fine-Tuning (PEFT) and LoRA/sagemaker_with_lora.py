from sagemaker.huggingface import HuggingFace

# Define hyperparameters
hyperparameters = {
    'model_id': 'meta-llama/Llama-2-7b-hf',
    'lora_r': 16,
    'lora_alpha': 32,
    'lora_dropout': 0.05,
    'learning_rate': 2e-4,
    'num_train_epochs': 3,
    'per_device_train_batch_size': 4,
    'gradient_accumulation_steps': 4,
}

# Create HuggingFace estimator
huggingface_estimator = HuggingFace(
    entry_point='train_lora.py',
    source_dir='./scripts',
    instance_type='ml.g5.2xlarge',  # Single GPU sufficient with LoRA
    instance_count=1,
    role=role,
    transformers_version='4.36.0',
    pytorch_version='2.1.0',
    py_version='py310',
    hyperparameters=hyperparameters,
)

# Start training
huggingface_estimator.fit({'training': training_data_s3})