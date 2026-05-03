from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load large model
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-70b-hf",
    load_in_4bit=True,  # Use QLoRA for 70B model
    device_map="auto"
)

# Configure LoRA for medical domain
lora_config = LoraConfig(
    r2,
    lora_alphad,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    task_type="CAUSAL_LM"
)

# Create PEFT model
peft_model = get_peft_model(model, lora_config)
# Now train on medical data with significantly reduced memory