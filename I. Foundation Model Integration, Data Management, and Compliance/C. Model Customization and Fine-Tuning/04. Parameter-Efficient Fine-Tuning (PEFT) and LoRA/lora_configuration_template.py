from peft import LoraConfig

# Recommended starting configuration
config = LoraConfig(
    r,                    # Rank - start here, adjust as needed
    lora_alpha2,           # Typically 2x rank
    target_modules=[         # Model-specific - check architecture
        "q_proj", "k_proj",
        "v_proj", "o_proj"
    ],
    lora_dropout=0.05,       # Light regularization
    bias="none",             # Usually don't train biases
    task_type="CAUSAL_LM"    # Or SEQ_2_SEQ_LM for T5-style
)