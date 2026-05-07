import boto3
import json

bedrock_data = boto3.client('bedrock-data-automation')

# Create data automation job
response = bedrock_data.invoke_data_automation_async(
    inputConfiguration={
        'document': {
            's3Uri': 's3://my-bucket/documents/contract.pdf'
        }
    },
    outputConfiguration={
        's3Uri': 's3://my-bucket/processed-output/',
        'format': 'JSON'
    },
    dataAutomationConfiguration={
        'document': {
            'splitterConfiguration': {
                'state': 'ENABLED'  # Enable chunking
            },
            'extractionTypes': ['TEXT', 'TABLE', 'KEY_VALUE']
        }
    }
)

job_arn = response['invocationArn']

# Check status
status_response = bedrock_data.get_data_automation_status(
    invocationArn=job_arn
)
print(f"Status: {status_response['status']}")