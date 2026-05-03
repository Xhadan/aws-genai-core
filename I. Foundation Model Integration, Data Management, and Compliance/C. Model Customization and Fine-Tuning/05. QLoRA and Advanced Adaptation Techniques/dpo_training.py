from trl import DPOTrainer, DPOConfig
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load SFT-trained model
model = AutoModelForCausalLM.from_pretrained("my-sft-model")
tokenizer = AutoTokenizer.from_pretrained("my-sft-model")

# DPO configuration
dpo_config = DPOConfig(
    beta=0.1,                    # KL divergence weight
    learning_rate^-7,          # Low learning rate for DPO
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    num_train_epochs=1,
    output_dir="./dpo-output",
)

# Preference dataset format
# Each example: {"prompt": str, "chosen": str, "rejected": str}

trainer = DPOTrainer(
    model=model,
    ref_model=None,  # Will use implicit reference
    args=dpo_config,
    train_dataset=preference_dataset,
    tokenizer=tokenizer,
)

trainer.train()