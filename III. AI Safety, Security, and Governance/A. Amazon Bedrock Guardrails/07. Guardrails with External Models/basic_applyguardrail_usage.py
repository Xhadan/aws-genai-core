import boto3
import requests

bedrock_runtime = boto3.client('bedrock-runtime')

def apply_guardrail(text, guardrail_id, guardrail_version, source):
    """
    Apply guardrail to text content.
    source: 'INPUT' for prompts, 'OUTPUT' for responses
    """
    response = bedrock_runtime.apply_guardrail(
        guardrailIdentifier=guardrail_id,
        guardrailVersion=guardrail_version,
        source=source,
        content=[
            {'text': {'text': text}}
        ]
    )

    return {
        'action': response['action'],
        'blocked': response['action'] = 'GUARDRAIL_INTERVENED' and not response.get('outputs'),
        'anonymized': response['action'] = 'GUARDRAIL_INTERVENED' and response.get('outputs'),
        'safe_text': response['outputs'][0]['text'] if response.get('outputs') else text,
        'assessments': response.get('assessments', [])
    }

def call_external_llm(prompt, api_key, api_url):
    """
    Call an external LLM API (example: generic REST API).
    """
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    payload = {'prompt': prompt, 'max_tokens': 1024}

    response = requests.post(api_url, headers=headers, json=payload)
    return response.json()['text']

def safe_external_model_call(
    user_prompt,
    guardrail_id,
    guardrail_version,
    external_api_key,
    external_api_url,
    blocked_message="I cannot process this request."
):
    """
    Call external model with guardrail protection on both input and output.
    """
    # Step 1: Check input
    input_result = apply_guardrail(
        user_prompt, guardrail_id, guardrail_version, 'INPUT'
    )

    if input_result['blocked']:
        return {
            'success': False,
            'response': blocked_message,
            'reason': 'input_blocked'
        }

    # Use anonymized prompt if PII was detected
    safe_prompt = input_result['safe_text']

    # Step 2: Call external model
    try:
        model_response = call_external_llm(
            safe_prompt, external_api_key, external_api_url
        )
    except Exception as e:
        return {
            'success': False,
            'response': 'Model call failed',
            'reason': str(e)
        }

    # Step 3: Check output
    output_result = apply_guardrail(
        model_response, guardrail_id, guardrail_version, 'OUTPUT'
    )

    if output_result['blocked']:
        return {
            'success': False,
            'response': blocked_message,
            'reason': 'output_blocked'
        }

    return {
        'success': True,
        'response': output_result['safe_text'],
        'input_modified': input_result['anonymized'],
        'output_modified': output_result['anonymized']
    }

# Usage
result = safe_external_model_call(
    user_prompt="My email is john@example.com. What's the weather?",
    guardrail_id='your-guardrail-id',
    guardrail_version='1',
    external_api_key='your-api-key',
    external_api_url='https://api.example.com/v1/completions'
)

print(f"Success: {result['success']}")
print(f"Response: {result['response']}")