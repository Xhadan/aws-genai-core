import boto3
import json
import random

bedrock_runtime = boto3.client('bedrock-runtime')

def pairwise_compare(question: str, response_a: str, response_b: str) -> dict:
    """Compare two responses using LLM-as-Judge."""

    # Randomly assign positions to mitigate position bias
    if random.random() > 0.5:
        first, second = response_a, response_b
        mapping = {'A': 'original_a', 'B': 'original_b'}
    else:
        first, second = response_b, response_a
        mapping = {'A': 'original_b', 'B': 'original_a'}

    prompt = f"""Compare these two responses to the question and determine which is better.

QUESTION: {question}

RESPONSE A:
{first}

RESPONSE B:
{second}

EVALUATION CRITERIA:
- Accuracy and correctness
- Completeness of information
- Clarity and organization
- Helpfulness to the user

INSTRUCTIONS:
1. Analyze both responses against the criteria
2. Determine which response is better overall
3. Explain your reasoning

Return JSON format:
{{"winner": "A" or "B" or "tie", "reasoning": "explanation", "confidence": "high/medium/low"}}
"""

    result = bedrock_runtime.converse(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        messages=[{'role': 'user', 'content': [{'text': prompt}]}],
        inferenceConfig={'maxTokens': 500, 'temperature': 0.0}
    )

    evaluation = json.loads(result['output']['message']['content'][0]['text'])

    # Map back to original labels
    if evaluation['winner'] in mapping:
        evaluation['winner'] = mapping[evaluation['winner']]

    return evaluation

# Example: Compare outputs from two different models
question = "Explain the CAP theorem"
response_model_a = "CAP theorem states you can only have 2 of 3: Consistency, Availability, Partition tolerance."
response_model_b = """The CAP theorem, proposed by Eric Brewer, states that a distributed system can only provide two of three guarantees simultaneously:
1. Consistency: All nodes see the same data at the same time
2. Availability: Every request receives a response
3. Partition Tolerance: System continues despite network failures

In practice, partition tolerance is required, so you choose between CP (consistent) or AP (available) systems."""

comparison = pairwise_compare(question, response_model_a, response_model_b)
print(f"Winner: {comparison['winner']}")
print(f"Confidence: {comparison['confidence']}")
print(f"Reasoning: {comparison['reasoning']}")