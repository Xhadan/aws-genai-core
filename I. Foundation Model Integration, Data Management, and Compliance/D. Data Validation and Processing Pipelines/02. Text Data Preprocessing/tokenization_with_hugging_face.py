from transformers import AutoTokenizer

# Load tokenizer matching your model
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")

text = "Amazon Bedrock provides access to foundation models."

# Tokenize
tokens = tokenizer.tokenize(text)
# ['▁Amazon', '▁Bed', 'rock', '▁provides', '▁access', '▁to', '▁foundation', '▁models', '.']

# Token IDs
token_ids = tokenizer.encode(text, return_tensors="pt")

# Count tokens (important for cost estimation)
token_count = len(tokenizer.encode(text))
print(f"Token count: {token_count}")  # Output: 10