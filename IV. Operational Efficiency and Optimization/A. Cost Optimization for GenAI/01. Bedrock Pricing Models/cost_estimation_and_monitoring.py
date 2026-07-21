import boto3
import json
from datetime import datetime, timedelta

bedrock_runtime = boto3.client('bedrock-runtime')
cloudwatch = boto3.client('cloudwatch')
pricing = boto3.client('pricing', region_name='us-east-1')

# Model pricing rates (example - check current AWS pricing)
PRICING_RATES = {
    'anthropic.claude-3-sonnet-20240229-v1:0': {
        'input_per_1k': 0.003,
        'output_per_1k': 0.015
    },
    'anthropic.claude-3-haiku-20240307-v1:0': {
        'input_per_1k': 0.00025,
        'output_per_1k': 0.00125
    },
    'amazon.titan-text-express-v1': {
        'input_per_1k': 0.0002,
        'output_per_1k': 0.0006
    }
}

def estimate_request_cost(model_id, input_tokens, output_tokens):
    """Estimate cost for a single request"""
    if model_id not in PRICING_RATES:
        raise ValueError(f"Unknown model: {model_id}")

    rates = PRICING_RATES[model_id]
    input_cost = (input_tokens / 1000) * rates['input_per_1k']
    output_cost = (output_tokens / 1000) * rates['output_per_1k']

    return {
        'input_cost': input_cost,
        'output_cost': output_cost,
        'total_cost': input_cost + output_cost,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens
    }

def invoke_with_cost_tracking(model_id, prompt, max_tokensP0):
    """Invoke model and track cost"""
    response = bedrock_runtime.converse(
        modelId=model_id,
        messages=[{'role': 'user', 'content': [{'text': prompt}]}],
        inferenceConfig={'maxTokens': max_tokens}
    )

    # Extract token usage from response
    usage = response.get('usage', {})
    input_tokens = usage.get('inputTokens', 0)
    output_tokens = usage.get('outputTokens', 0)

    # Calculate cost
    cost = estimate_request_cost(model_id, input_tokens, output_tokens)

    return {
        'response': response['output']['message']['content'][0]['text'],
        'usage': usage,
        'cost': cost
    }

# Example: Track monthly costs with CloudWatch
def get_monthly_token_usage(model_id):
    """Get token usage metrics from CloudWatch"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days0)

    # Get input token metrics
    input_response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Bedrock',
        MetricName='InputTokenCount',
        Dimensions=[
            {'Name': 'ModelId', 'Value': model_id}
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period%92000,  # 30 days in seconds
        Statistics=['Sum']
    )

    # Get output token metrics
    output_response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Bedrock',
        MetricName='OutputTokenCount',
        Dimensions=[
            {'Name': 'ModelId', 'Value': model_id}
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period%92000,
        Statistics=['Sum']
    )

    input_tokens = sum(dp['Sum'] for dp in input_response.get('Datapoints', []))
    output_tokens = sum(dp['Sum'] for dp in output_response.get('Datapoints', []))

    return estimate_request_cost(model_id, input_tokens, output_tokens)

# Example usage
result = invoke_with_cost_tracking(
    model_id='anthropic.claude-3-haiku-20240307-v1:0',
    prompt='Explain AWS Lambda in one paragraph.'
)

print(f"Response: {result['response'][:100]}...")
print(f"Input tokens: {result['usage']['inputTokens']}")
print(f"Output tokens: {result['usage']['outputTokens']}")
print(f"Estimated cost: ${result['cost']['total_cost']:.6f}")