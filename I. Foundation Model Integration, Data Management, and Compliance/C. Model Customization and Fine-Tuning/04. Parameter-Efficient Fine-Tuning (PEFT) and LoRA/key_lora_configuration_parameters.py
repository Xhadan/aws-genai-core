from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r,                          # Rank of decomposition matrices
    lora_alpha2,                 # Scaling factor
    target_modules=[               # Layers to apply LoRA
        "q_proj",                  # Query projection
        "k_proj",                  # Key projection
        "v_proj",                  # Value projection
        "o_proj",                  # Output projection
    ],
    lora_dropout=0.05,             # Dropout rate
    bias="none",                   # Don't train bias terms
    task_type="CAUSAL_LM"          # Task type for language models
)

# Wrap base model with LoRA
model = get_peft_model(base_model, lora_config)
model.print_trainable_parameters()
# Output: trainable params: 4,194,304 || all params: 6,742,609,920 || trainable%: 0.06%