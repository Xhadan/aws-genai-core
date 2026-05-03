from sagemaker.huggingface import HuggingFace

hyperparameters = {
    'model_id': 'meta-llama/Llama-2-70b-hf',
    'use_4bit': True,
    'bnb_4bit_quant_type': 'nf4',
    'use_double_quant': True,
    'lora_r': 16,
    'lora_alpha': 32,
    'learning_rate': 2e-4,
    'num_train_epochs': 1,
    'per_device_train_batch_size': 1,
    'gradient_accumulation_steps': 16,
}

huggingface_estimator = HuggingFace(
    entry_point='train_qlora.py',
    source_dir='./scripts',
    instance_type='ml.g5.12xlarge',  # Single A10G GPU
    instance_count=1,
    role=role,
    transformers_version='4.36.0',
    pytorch_version='2.1.0',
    py_version='py310',
    hyperparameters=hyperparameters,
)