import boto3

bedrock = boto3.client('bedrock')

response = bedrock.create_inference_profile(
    inferenceProfileName='customer-support-app',
    description='Profile for customer support chatbot',
    modelSource={
        'copyFrom': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0'
    },
    tags=[
        {'key': 'Team', 'value': 'CustomerSupport'},
        {'key': 'CostCenter', 'value': 'CS-001'},
        {'key': 'Environment', 'value': 'Production'}
    ]
)

profile_arn = response['inferenceProfileArn']