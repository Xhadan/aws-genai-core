import boto3

bedrock = boto3.client('bedrock')

response = bedrock.create_model_customization_job(
    jobName='customer-support-sft',
    customModelName='titan-support-assistant',
    roleArn='arn:aws:iam::123456789012:role/BedrockCustomizationRole',
    baseModelIdentifier='amazon.titan-text-express-v1',
    customizationType='FINE_TUNING',
    trainingDataConfig={
        's3Uri': 's3://my-bucket/training/training.jsonl'
    },
    validationDataConfig={
        's3Uri': 's3://my-bucket/training/validation.jsonl'
    },
    outputDataConfig={
        's3Uri': 's3://my-bucket/output/'
    },
    hyperParameters={
        'epochCount': '3',
        'batchSize': '8',
        'learningRate': '0.00001',
        'learningRateWarmupSteps': '100'
    }
)

print(f"Job ARN: {response['jobArn']}")