import boto3

bedrock = boto3.client('bedrock')

def create_encrypted_custom_model(
    base_model_id,
    training_data_s3_uri,
    output_s3_uri,
    kms_key_arn,
    job_name='encrypted-fine-tune'
):
    """
    Create fine-tuning job with customer-managed encryption key.
    """
    response = bedrock.create_model_customization_job(
        jobName=job_name,
        customModelName=f'{job_name}-model',
        roleArn='arn:aws:iam::123456789012:role/BedrockCustomizationRole',
        baseModelIdentifierse_model_id,

        # Training configuration
        trainingDataConfig={
            's3Uri': training_data_s3_uri
        },
        outputDataConfig={
            's3Uri': output_s3_uri
        },

        # Use customer-managed KMS key
        customModelKmsKeyId=kms_key_arn,

        # Hyperparameters
        hyperParameters={
            'epochCount': '3',
            'batchSize': '4',
            'learningRate': '0.00001'
        },

        customizationType='FINE_TUNING',

        # Tags
        jobTags=[
            {'key': 'Encrypted', 'value': 'true'},
            {'key': 'KeyArn', 'value': kms_key_arn}
        ]
    )

    print(f"Created job: {response['jobArn']}")
    return response['jobArn']

# Create fine-tuning job with encryption
job_arn = create_encrypted_custom_model(
    base_model_id='amazon.titan-text-express-v1',
    training_data_s3_uri='s3://my-training-data/dataset.jsonl',
    output_s3_uri='s3://my-model-artifacts/',
    kms_key_arn='arn:aws:kms:us-east-1:123456789012:key/custom-model-key'
)