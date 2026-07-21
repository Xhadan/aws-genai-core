import boto3
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

bedrock_runtime = boto3.client('bedrock-runtime')

def batch_classify_efficient(items, model_id='anthropic.claude-3-haiku-20240307-v1:0'):
    """
    Efficiently classify multiple items in single requests.
    Groups items to maximize tokens per request while staying under limits.
    """

    # Group items into batches (10 items per request for efficiency)
    batch_size = 10
    batches = [items[i:i+batch_size] for i in range(0, len(items), batch_size)]

    results = []

    for batch in batches:
        # Create efficient multi-item prompt
        items_text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(batch)])

        prompt = f"""Classify each item's sentiment. Return JSON array with format:
[{{"id": 1, "sentiment": "positive|negative|neutral"}}]

Items:
{items_text}"""

        response = bedrock_runtime.converse(
            modelId=model_id,
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={
                'maxTokens': len(batch) * 30,  # ~30 tokens per result
                'temperature': 0
            }
        )

        # Parse batch results
        try:
            batch_results = json.loads(
                response['output']['message']['content'][0]['text']
            )
            results.extend(batch_results)
        except json.JSONDecodeError:
            # Handle parsing errors
            pass

    return results


def parallel_batch_processing(items, max_workers=5):
    """Process batches in parallel for throughput"""
    batch_size = 10
    batches = [items[i:i+batch_size] for i in range(0, len(items), batch_size)]

    all_results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_batch, batch): i
            for i, batch in enumerate(batches)
        }

        for future in as_completed(futures):
            batch_idx = futures[future]
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                print(f"Batch {batch_idx} failed: {e}")

    return all_results


def process_single_batch(batch):
    """Process a single batch of items"""
    return batch_classify_efficient(batch)


# Compare token usage: individual vs batch
def compare_efficiency():
    """Demonstrate batch efficiency gains"""
    test_items = [
        "Great product, love it!",
        "Terrible experience, never again",
        "It works as described",
        "Amazing quality for the price",
        "Disappointed with shipping time"
    ]

    # Method 1: Individual requests
    individual_tokens = 0
    for item in test_items:
        prompt = f"Classify sentiment as positive/negative/neutral: {item}"
        # Estimate: ~20 tokens per request + ~10 tokens response
        individual_tokens += 30

    # Method 2: Batch request
    batch_prompt = "Classify sentiment for each:\n" + "\n".join(test_items)
    # Estimate: ~40 tokens for prompt + ~50 tokens response
    batch_tokens = 90

    print(f"Individual requests: ~{individual_tokens * len(test_items)} tokens")
    print(f"Batch request: ~{batch_tokens} tokens")
    print(f"Savings: {((individual_tokens * len(test_items)) - batch_tokens) / (individual_tokens * len(test_items)) * 100:.1f}%")


compare_efficiency()