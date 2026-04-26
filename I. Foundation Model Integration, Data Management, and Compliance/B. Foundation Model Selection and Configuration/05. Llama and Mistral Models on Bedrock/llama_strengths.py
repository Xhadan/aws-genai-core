import boto3
import json

bedrock = boto3.client('bedrock-runtime')

def invoke_llama(prompt, model_size='70b'):
    """Invoke Llama model via Bedrock."""

    model_id = f'meta.llama3-1-{model_size}-instruct-v1:0'

    response = bedrock.converse(
        modelId=model_id,
        messages=[
            {'role': 'user', 'content': [{'text': prompt}]}
        ],
        inferenceConfig={
            'maxTokens': 2048,
            'temperature': 0.7,
            'topP': 0.9
        }
    )

    return response['output']['message']['content'][0]['text']

# Use Llama for multilingual content
response = invoke_llama(
    "Translate this to French, Spanish, and German: Hello, welcome to our service!",
    model_size='70b'
)