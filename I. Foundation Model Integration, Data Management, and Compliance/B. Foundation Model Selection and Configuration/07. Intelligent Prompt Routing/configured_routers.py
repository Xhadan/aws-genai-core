import boto3

bedrock = boto3.client('bedrock-runtime')

def invoke_with_routing(prompt):
    """Invoke using Intelligent Prompt Router."""

    # Use the router ARN instead of specific model
    response = bedrock.converse(
        modelId='arn:aws:bedrock:us-east-1:123456789012:inference-profile/my-claude-router',
        messages=[
            {'role': 'user', 'content': [{'text': prompt}]}
        ],
        inferenceConfig={
            'maxTokens': 1024
        }
    )

    # Check which model was used (available in response metadata)
    model_used = response.get('modelId', 'Unknown')
    output = response['output']['message']['content'][0]['text']

    return {
        'response': output,
        'model_used': model_used
    }

# Simple query - likely routes to Haiku
simple = invoke_with_routing("What is AWS?")
print(f"Simple query routed to: {simple['model_used']}")

# Complex query - likely routes to Sonnet
complex_prompt = """
Analyze the following contract clause and identify potential liability
risks for the vendor. Consider regulatory compliance, indemnification
terms, and limitation of liability provisions...
"""
complex_result = invoke_with_routing(complex_prompt)
print(f"Complex query routed to: {complex_result['model_used']}")