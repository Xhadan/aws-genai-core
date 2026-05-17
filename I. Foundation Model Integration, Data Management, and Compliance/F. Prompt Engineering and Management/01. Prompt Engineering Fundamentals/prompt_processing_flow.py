import boto3
import json

bedrock = boto3.client('bedrock-runtime')

def create_structured_prompt(task, context=None, format_instructions=None):
    """Create a well-structured prompt following best practices."""

    # Build system message with role and guidelines
    system_message = """You are an expert AWS solutions architect with deep knowledge
of cloud services, best practices, and cost optimization. Provide accurate,
practical advice based on AWS Well-Architected Framework principles.

Guidelines:
- Be concise but comprehensive
- Include specific AWS service names
- Mention relevant security considerations
- Provide code examples when applicable"""

    # Build user message with structure
    user_content = ""

    if context:
        user_content += f"<context>\n{context}\n</context>\n\n"

    user_content += f"<task>\n{task}\n</task>"

    if format_instructions:
        user_content += f"\n\n<format>\n{format_instructions}\n</format>"

    return system_message, user_content


def invoke_with_structured_prompt(task, context=None, format_instructions=None):
    """Invoke Bedrock with a structured prompt."""

    system_message, user_content = create_structured_prompt(
        task, context, format_instructions
    )

    response = bedrock.converse(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        messages=[
            {
                "role": "user",
                "content": [{"text": user_content}]
            }
        ],
        system=[{"text": system_message}],
        inferenceConfig={
            "maxTokens": 2048,
            "temperature": 0.7
        }
    )

    return response['output']['message']['content'][0]['text']


# Example usage
result = invoke_with_structured_prompt(
    task="Design a serverless API architecture for a mobile application",
    context="The app has 10,000 daily active users, needs real-time notifications, and stores user data requiring encryption at rest",
    format_instructions="Provide a numbered list of AWS services with brief explanations, then a simple architecture diagram in ASCII"
)

print(result)