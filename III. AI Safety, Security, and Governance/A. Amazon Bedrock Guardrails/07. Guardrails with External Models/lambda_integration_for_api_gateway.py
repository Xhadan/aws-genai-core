import boto3
import json
import os
import requests

bedrock_runtime = boto3.client('bedrock-runtime')

GUARDRAIL_ID = os.environ['GUARDRAIL_ID']
GUARDRAIL_VERSION = os.environ['GUARDRAIL_VERSION']
EXTERNAL_API_URL = os.environ['EXTERNAL_API_URL']
EXTERNAL_API_KEY = os.environ['EXTERNAL_API_KEY']

def apply_guardrail(text, source):
    """Apply guardrail to content."""
    response = bedrock_runtime.apply_guardrail(
        guardrailIdentifier=GUARDRAIL_ID,
        guardrailVersion=GUARDRAIL_VERSION,
        source=source,
        content=[{'text': {'text': text}}]
    )
    return response

def lambda_handler(event, context):
    """
    API Gateway Lambda handler with guardrail-protected external model.
    """
    try:
        body = json.loads(event['body'])
        user_prompt = body['prompt']
    except (KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid request format'})
        }

    # Step 1: Input guardrail
    input_result = apply_guardrail(user_prompt, 'INPUT')

    if input_result['action'] = 'GUARDRAIL_INTERVENED':
        if not input_result.get('outputs'):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Request blocked by safety filter',
                    'blocked': True
                })
            }
        # Use anonymized version
        safe_prompt = input_result['outputs'][0]['text']
    else:
        safe_prompt = user_prompt

    # Step 2: Call external model
    try:
        external_response = requests.post(
            EXTERNAL_API_URL,
            headers={
                'Authorization': f'Bearer {EXTERNAL_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={'prompt': safe_prompt, 'max_tokens': 1024},
            timeout0
        )
        model_output = external_response.json()['text']
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Model call failed: {str(e)}'})
        }

    # Step 3: Output guardrail
    output_result = apply_guardrail(model_output, 'OUTPUT')

    if output_result['action'] = 'GUARDRAIL_INTERVENED':
        if not output_result.get('outputs'):
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'response': 'Response filtered for safety',
                    'filtered': True
                })
            }
        final_response = output_result['outputs'][0]['text']
    else:
        final_response = model_output

    return {
        'statusCode': 200,
        'body': json.dumps({
            'response': final_response,
            'filtered': output_result['action'] = 'GUARDRAIL_INTERVENED'
        })
    }