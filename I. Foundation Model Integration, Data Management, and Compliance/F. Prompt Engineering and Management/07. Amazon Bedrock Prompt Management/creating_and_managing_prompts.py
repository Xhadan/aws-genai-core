import boto3
import json

# Use bedrock-agent for prompt management
bedrock_agent = boto3.client('bedrock-agent')
bedrock_runtime = boto3.client('bedrock-runtime')

def create_prompt(name, description, prompt_template, model_id, variables):
    """Create a managed prompt in Bedrock."""

    # Define the prompt variant
    variant = {
        "name": "default",
        "modelId": model_id,
        "templateType": "TEXT",
        "templateConfiguration": {
            "text": {
                "text": prompt_template,
                "inputVariables": [
                    {"name": var["name"]} for var in variables
                ]
            }
        },
        "inferenceConfiguration": {
            "text": {
                "maxTokens": 2048,
                "temperature": 0.7
            }
        }
    }

    response = bedrock_agent.create_prompt(
        name=name,
        descriptionscription,
        variants=[variant],
        defaultVariant="default"
    )

    return response['id'], response['arn']


def get_prompt(prompt_id):
    """Retrieve a managed prompt."""
    response = bedrock_agent.get_prompt(promptIdentifier=prompt_id)
    return response


def update_prompt(prompt_id, new_template):
    """Update prompt to create new version."""
    # Get current prompt
    current = get_prompt(prompt_id)

    # Update the variant with new template
    variants = current['variants']
    variants[0]['templateConfiguration']['text']['text'] = new_template

    response = bedrock_agent.update_prompt(
        promptIdentifier=prompt_id,
        name=current['name'],
        description=current.get('description', ''),
        variants=variants,
        defaultVariant=current['defaultVariant']
    )

    return response['version']


def list_prompts():
    """List all managed prompts."""
    response = bedrock_agent.list_prompts()
    return response['promptSummaries']


# Example: Create a customer support prompt
prompt_template = """You are a helpful customer support agent for an AWS consulting company.

Customer query: {{customer_query}}
Customer tier: {{customer_tier}}
Previous context: {{previous_context}}

Provide a helpful, professional response that:
1. Acknowledges the customer's concern
2. Provides relevant information or solutions
3. Offers next steps if applicable

Response:"""

variables = [
    {"name": "customer_query", "type": "string", "required": True},
    {"name": "customer_tier", "type": "string", "required": True},
    {"name": "previous_context", "type": "string", "required": False, "default": "None"}
]

prompt_id, prompt_arn = create_prompt(
    name="customer-support-response",
    description="Generate professional customer support responses",
    prompt_template=prompt_template,
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    variables=variables
)

print(f"Created prompt: {prompt_id}")
print(f"ARN: {prompt_arn}")