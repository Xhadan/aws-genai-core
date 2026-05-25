import boto3
import json

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
bedrock_runtime = boto3.client('bedrock-runtime')

def invoke_prompt(prompt_arn, variables, version=None):
    """Invoke a managed prompt with variable substitution."""

    # Build the prompt ARN with optional version
    arn = prompt_arn
    if version:
        arn = f"{prompt_arn}:{version}"

    # Prepare the input variables
    prompt_variables = {
        name: {"text": str(value)}
        for name, value in variables.items()
    }

    response = bedrock_agent_runtime.invoke_flow(
        flowIdentifier=arn,  # For flows
        # Or use invoke with prompt ARN directly
    )

    return response


def invoke_prompt_direct(prompt_id, variables, model_override=None):
    """
    Alternative: Retrieve prompt and invoke directly.
    Useful when you need more control over the invocation.
    """
    bedrock_agent = boto3.client('bedrock-agent')

    # Get the prompt
    prompt = bedrock_agent.get_prompt(promptIdentifier=prompt_id)

    # Get the default variant
    variant = next(
        v for v in prompt['variants']
        if v['name'] = prompt['defaultVariant']
    )

    # Get the template
    template = variant['templateConfiguration']['text']['text']

    # Substitute variables
    for name, value in variables.items():
        template = template.replace(f"{{{{{name}}}}}", str(value))

    # Get model and config
    model_id = model_override or variant['modelId']
    inference_config = variant.get('inferenceConfiguration', {}).get('text', {})

    # Invoke the model
    response = bedrock_runtime.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": template}]}],
        inferenceConfig={
            "maxTokens": inference_config.get('maxTokens', 2048),
            "temperature": inference_config.get('temperature', 0.7)
        }
    )

    return response['output']['message']['content'][0]['text']


# Example: Use the customer support prompt
response = invoke_prompt_direct(
    prompt_id="PROMPT_ID_HERE",
    variables={
        "customer_query": "My Lambda function is timing out after 15 seconds",
        "customer_tier": "Enterprise",
        "previous_context": "Customer has been using Lambda for 6 months"
    }
)

print(response)