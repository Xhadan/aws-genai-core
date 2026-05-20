import boto3
from collections import Counter
import re

bedrock = boto3.client('bedrock-runtime')

def generate_cot_response(prompt, temperature=0.7):
    """Generate a single chain-of-thought response."""
    response = bedrock.converse(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={
            "maxTokens": 1024,
            "temperature": temperature
        }
    )
    return response['output']['message']['content'][0]['text']


def extract_final_answer(response):
    """Extract the final answer from a CoT response."""
    # Look for patterns like "Answer: X" or "Therefore, X" or "Final answer: X"
    patterns = [
        r"(?:final answer|answer|therefore|thus)[:\s]+([^\n]+)",
        r"(?:=\s*)(\$?[\d,]+(?:\.\d+)?)",
        r"(?:is\s+)(\$?[\d,]+(?:\.\d+)?)"
    ]

    for pattern in patterns:
        match = re.search(pattern, response.lower())
        if match:
            return match.group(1).strip()

    # Return last line as fallback
    lines = response.strip().split('\n')
    return lines[-1].strip()


def self_consistency(question, num_samples=5, temperature=0.7):
    """Apply self-consistency prompting with majority voting."""

    prompt = f"""{question}

Let's solve this step by step, then clearly state the final answer."""

    # Generate multiple reasoning paths
    responses = []
    answers = []

    for i in range(num_samples):
        response = generate_cot_response(prompt, temperature)
        responses.append(response)
        answer = extract_final_answer(response)
        answers.append(answer)

    # Majority voting
    counter = Counter(answers)
    winning_answer, vote_count = counter.most_common(1)[0]
    confidence = vote_count / num_samples

    return {
        'answer': winning_answer,
        'confidence': confidence,
        'vote_distribution': dict(counter),
        'all_responses': responses
    }


# Example: Math problem with self-consistency
question = """
A company has 3 AWS accounts. Account A has 15 EC2 instances, Account B has 23 instances,
and Account C has 12 instances. If they consolidate to 2 accounts and distribute instances
evenly (rounding up when needed), what's the maximum instances in any single account?
"""

result = self_consistency(question, num_samples=5)

print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']:.0%}")
print(f"Vote Distribution: {result['vote_distribution']}")