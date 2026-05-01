import boto3

bedrock = boto3.client('bedrock')

# Create CPT customization job
response = bedrock.create_model_customization_job(
    jobName='medical-domain-cpt',
    customModelName='titan-text-medical',
    roleArn='arn:aws:iam::123456789012:role/BedrockCustomizationRole',
    baseModelIdentifier='amazon.titan-text-express-v1',
    customizationType='CONTINUED_PRE_TRAINING',
    trainingDataConfig={
        's3Uri': 's3://my-bucket/training-data/'
    },
    outputDataConfig={
        's3Uri': 's3://my-bucket/output/'
    },
    hyperParameters={
        'epochCount': '1',
        'batchSize': '8',
        'learningRate': '0.000001'
    }
)