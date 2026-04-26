import boto3
import json

bedrock = boto3.client('bedrock-runtime')

def invoke_claude_with_thinking(prompt, use_extended_thinkinglse):
    """Invoke Claude with optional extended thinking."""

    messages = [{"role": "user", "content": [{"text": prompt}]}]

    # For extended thinking (Claude 3.7+), add system instruction
    system = []
    if use_extended_thinking:
        system = [{
            "text": "Think step-by-step through this problem. Show your reasoning process before providing your final answer."
        }]

    response = bedrock.converse(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        messages=messages,
        system=system,
        inferenceConfig={
            "maxTokens": 4096,
            "temperature": 0  # Lower for reasoning tasks
        }
    )

    return response['output']['message']['content'][0]['text']

# Simple query - standard mode
simple_answer = invoke_claude_with_thinking(
    "What is the capital of France?"
)

# Complex query - extended thinking
complex_answer = invoke_claude_with_thinking(
    "Design a distributed system architecture for a real-time bidding platform handling 1M requests/second.",
    use_extended_thinking=True
)