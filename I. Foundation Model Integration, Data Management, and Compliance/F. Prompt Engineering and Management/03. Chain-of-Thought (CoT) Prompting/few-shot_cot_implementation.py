import boto3

bedrock = boto3.client('bedrock-runtime')

def few_shot_cot(question, examples, model_id='anthropic.claude-3-5-sonnet-20241022-v2:0'):
    """Apply few-shot chain-of-thought with example reasoning chains."""

    # Build examples with reasoning chains
    examples_text = ""
    for i, ex in enumerate(examples, 1):
        examples_text += f"""Example {i}:
Question: {ex['question']}
Reasoning: {ex['reasoning']}
Answer: {ex['answer']}

"""

    prompt = f"""I'll solve problems by showing my reasoning step by step.

{examples_text}Now solve this:
Question: {question}
Reasoning:"""

    response = bedrock.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={
            "maxTokens": 2048,
            "temperature": 0
        }
    )

    return response['output']['message']['content'][0]['text']


# Define examples with reasoning chains
aws_cost_examples = [
    {
        "question": "If an S3 bucket has 100GB of data and receives 1 million GET requests per month, what's the monthly storage cost? (Standard storage: $0.023/GB, GET requests: $0.0004/1000 requests)",
        "reasoning": """Let me calculate this step by step:
1. Storage cost: 100 GB * $0.023/GB = $2.30
2. Request cost: 1,000,000 requests / 1000 * $0.0004 = $0.40
3. Total monthly cost: $2.30 + $0.40 = $2.70""",
        "answer": "$2.70 per month"
    },
    {
        "question": "A Lambda function runs 5 million times per month, with average duration of 200ms and 256MB memory. What's the monthly compute cost? (Free tier: 1M requests, 400,000 GB-seconds. Price: $0.20/1M requests, $0.0000166667/GB-second)",
        "reasoning": """Let me break this down:
1. Request charges:
   - Billable requests: 5M - 1M (free tier) = 4M requests
   - Cost: 4 * $0.20 = $0.80

2. Compute charges:
   - GB-seconds per invocation: 0.256 GB * 0.2 seconds = 0.0512 GB-seconds
   - Total GB-seconds: 5M * 0.0512 = 256,000 GB-seconds
   - Billable GB-seconds: 256,000 - 400,000 = 0 (within free tier)
   - Compute cost: $0

3. Total: $0.80 + $0 = $0.80""",
        "answer": "$0.80 per month"
    }
]

# Use few-shot CoT for a new problem
new_question = """
A DynamoDB table has 50GB of data with provisioned capacity of 100 RCU and 50 WCU.
Monthly pricing: $0.25/GB storage, $0.00065/RCU-hour, $0.00065/WCU-hour.
What's the monthly cost?
"""

result = few_shot_cot(new_question, aws_cost_examples)
print(result)