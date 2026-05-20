import boto3

bedrock = boto3.client('bedrock-runtime')

def zero_shot_cot(question, model_id='anthropic.claude-3-5-sonnet-20241022-v2:0'):
    """Apply zero-shot chain-of-thought prompting."""

    prompt = f"""{question}

Let's think through this step by step."""

    response = bedrock.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={
            "maxTokens": 2048,
            "temperature": 0  # Lower temperature for reasoning
        }
    )

    return response['output']['message']['content'][0]['text']


def cot_with_format(question, model_id='anthropic.claude-3-5-sonnet-20241022-v2:0'):
    """CoT with explicit format requirements."""

    prompt = f"""Question: {question}

Please solve this step by step:
1. First, identify what we know
2. Then, determine what we need to find
3. Show each calculation or reasoning step
4. Finally, state the answer clearly

Begin your analysis:"""

    response = bedrock.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={
            "maxTokens": 2048,
            "temperature": 0
        }
    )

    return response['output']['message']['content'][0]['text']


# Example: AWS Cost Calculation
question = """
A company runs 10 m5.xlarge EC2 instances 24/7 in us-east-1.
On-demand price is $0.192/hour. They can commit to Reserved Instances
for 40% savings or use Spot instances for 70% savings (but only for
6 instances due to availability). What's the optimal monthly cost?
"""

# Zero-shot CoT
print("== Zero-Shot CoT ==")
answer = zero_shot_cot(question)
print(answer)

# CoT with structured format
print("\n== Structured CoT ==")
structured_answer = cot_with_format(question)
print(structured_answer)