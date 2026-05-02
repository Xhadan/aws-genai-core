import json
import random

# Load your dataset
with open('labeled_data.jsonl', 'r') as f:
    data = [json.loads(line) for line in f]

# Shuffle data
random.shuffle(data)

# Split 90/10 for training/validation
split_idx = int(len(data) * 0.9)
training_data = data[:split_idx]
validation_data = data[split_idx:]

# Write split files
with open('training.jsonl', 'w') as f:
    for item in training_data:
        f.write(json.dumps(item) + '\n')

with open('validation.jsonl', 'w') as f:
    for item in validation_data:
        f.write(json.dumps(item) + '\n')