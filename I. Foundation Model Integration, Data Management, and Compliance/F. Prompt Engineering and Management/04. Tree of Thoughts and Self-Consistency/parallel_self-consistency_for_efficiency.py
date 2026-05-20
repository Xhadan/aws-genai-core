import boto3
import asyncio
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import re

bedrock = boto3.client('bedrock-runtime')

def generate_single_response(args):
    """Generate one response (for thread pool)."""
    prompt, temperature = args
    response = bedrock.converse(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={
            "maxTokens": 1024,
            "temperature": temperature
        }
    )
    return response['output']['message']['content'][0]['text']


def parallel_self_consistency(question, num_samples, temperature=0.7, max_workers=5):
    """
    Run self-consistency with parallel API calls for faster execution.
    Uses ThreadPoolExecutor for concurrent Bedrock calls.
    """
    prompt = f"""{question}

Solve this step by step. End with "Final Answer: [your answer]"."""

    # Prepare arguments for parallel execution
    args = [(prompt, temperature) for _ in range(num_samples)]

    # Execute in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        responses = list(executor.map(generate_single_response, args))

    # Extract answers
    answers = []
    for response in responses:
        match = re.search(r'final answer[:\s]+(.+?)(?:\n|$)', response.lower())
        if match:
            answers.append(match.group(1).strip())
        else:
            # Fallback: try to find a number or last line
            numbers = re.findall(r'\$?[\d,]+(?:\.\d+)?', response)
            if numbers:
                answers.append(numbers[-1])

    # Majority voting with confidence
    if not answers:
        return {'answer': None, 'confidence': 0, 'distribution': {}}

    counter = Counter(answers)
    winner, count = counter.most_common(1)[0]

    return {
        'answer': winner,
        'confidence': count / len(answers),
        'distribution': dict(counter),
        'num_valid_answers': len(answers),
        'total_samples': num_samples
    }


# Example: Complex calculation with parallel self-consistency
question = """
A company uses AWS with the following monthly costs:
- 10 t3.large instances at $0.0832/hour running 24/7
- 500GB EBS gp3 storage at $0.08/GB
- 2TB S3 Standard storage at $0.023/GB
- 5TB data transfer out at $0.09/GB
- 1M Lambda invocations (128MB, 200ms avg) at $0.20/M requests + compute

Calculate the total monthly AWS bill.
"""

result = parallel_self_consistency(question, num_samples=7, max_workers=7)

print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']:.0%}")
print(f"Vote distribution: {result['distribution']}")