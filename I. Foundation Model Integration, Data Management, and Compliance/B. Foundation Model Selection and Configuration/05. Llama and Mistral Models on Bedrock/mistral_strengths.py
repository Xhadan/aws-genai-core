import boto3
import json

bedrock = boto3.client('bedrock-runtime')

def invoke_mistral(prompt, model='large'):
    """Invoke Mistral model via Bedrock."""

    model_ids = {
        'large': 'mistral.mistral-large-2407-v1:0',
        'mixtral': 'mistral.mixtral-8x7b-instruct-v0:1',
        'small': 'mistral.mistral-7b-instruct-v0:2'
    }

    response = bedrock.converse(
        modelId=model_ids[model],
        messages=[
            {'role': 'user', 'content': [{'text': prompt}]}
        ],
        inferenceConfig={
            'maxTokens': 2048,
            'temperature': 0.7
        }
    )

    return response['output']['message']['content'][0]['text']

# Use Mistral for cost-efficient processing
response = invoke_mistral(
    "Analyze this customer feedback and extract key themes: ...",
    model='mixtral'
)