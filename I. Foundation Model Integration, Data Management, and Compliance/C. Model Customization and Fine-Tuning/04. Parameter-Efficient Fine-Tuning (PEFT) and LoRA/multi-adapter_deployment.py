import boto3
import json

runtime = boto3.client('sagemaker-runtime')

# Invoke with specific adapter
response = runtime.invoke_endpoint(
    EndpointName='multi-lora-endpoint',
    ContentType='application/json',
    Body=json.dumps({
        'inputs': 'Summarize this medical report:',
        'adapter_id': 'medical-lora-v2',  # Specify which adapter
        'parameters': {
            'max_new_tokens': 256,
            'temperature': 0.7
        }
    })
)

result = json.loads(response['Body'].read().decode())