import boto3

bedrock = boto3.client('bedrock-runtime')

def cot_debug(code, error_description):
    """Use CoT to debug code step by step."""

    prompt = f"""You are an expert debugger. Analyze this code and error step by step.

Code:
```python
{code}
```

Error: {error_description}

Debug this step by step:
1. First, understand what the code is trying to do
2. Trace through the execution with sample values
3. Identify where the error would occur
4. Explain why the error happens
5. Propose a fix

Begin analysis:"""

    response = bedrock.converse(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={
            "maxTokens": 2048,
            "temperature": 0
        }
    )

    return response['output']['message']['content'][0]['text']


def cot_architecture_review(architecture_description):
    """Use CoT for architecture review and recommendations."""

    prompt = f"""Review this AWS architecture step by step.

Architecture:
{architecture_description}

Perform a systematic review:

Step 1: Security Analysis
- Identify security controls in place
- Find potential security gaps
- Check compliance considerations

Step 2: Reliability Analysis
- Identify single points of failure
- Check for multi-AZ/multi-region design
- Evaluate backup and recovery

Step 3: Performance Analysis
- Identify potential bottlenecks
- Check scaling capabilities
- Review caching strategies

Step 4: Cost Analysis
- Identify cost optimization opportunities
- Check for over-provisioning
- Suggest cost-effective alternatives

Step 5: Summary and Recommendations
- Prioritize improvements
- Provide specific action items

Begin review:"""

    response = bedrock.converse(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={
            "maxTokens": 4096,
            "temperature": 0
        }
    )

    return response['output']['message']['content'][0]['text']


# Example: Debug code
buggy_code = """
def calculate_discount(prices, discount_percent):
    total = 0
    for price in prices:
        discounted = price * (1 - discount_percent)
        total += discounted
    return total

# Usage
result = calculate_discount([100, 200, 300], 20)
print(f"Total: ${result}")
"""

debug_result = cot_debug(buggy_code, "The discount calculation gives wrong results. A 20% discount on $600 should give $480, but it gives a negative number.")
print(debug_result)