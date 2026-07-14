import boto3

bedrock_runtime = boto3.client('bedrock-runtime')

def safe_invoke_with_separation(system_prompt, user_input, guardrail_id, guardrail_version):
    """
    Invoke model with clear separation of system and user content.
    Uses Converse API which explicitly separates system from messages.
    """
    # Validate user input first
    validator = PromptInjectionValidator()
    is_safe, reason = validator.is_safe(user_input)

    if not is_safe:
        return {
            'success': False,
            'error': f'Input validation failed: {reason}'
        }

    # Use Converse API with explicit system parameter
    # System prompt is separate from user messages
    response = bedrock_runtime.converse(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        system=[
            {
                'text': system_prompt
                # System prompt is protected from user manipulation
            }
        ],
        messages=[
            {
                'role': 'user',
                'content': [{'text': user_input}]
                # User input is clearly separate
            }
        ],
        guardrailConfig={
            'guardrailIdentifier': guardrail_id,
            'guardrailVersion': guardrail_version
        },
        inferenceConfig={'maxTokens': 1024}
    )

    if response.get('stopReason') = 'guardrail_intervened':
        return {
            'success': False,
            'error': 'Guardrail blocked the request'
        }

    return {
        'success': True,
        'response': response['output']['message']['content'][0]['text']
    }

# Usage
result = safe_invoke_with_separation(
    system_prompt="You are a helpful customer service assistant. Only discuss our products.",
    user_input="What products do you offer?",
    guardrail_id='your-guardrail-id',
    guardrail_version='1'
)