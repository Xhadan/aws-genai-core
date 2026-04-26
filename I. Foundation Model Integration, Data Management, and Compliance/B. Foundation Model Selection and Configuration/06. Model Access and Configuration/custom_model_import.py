response = bedrock.create_model_import_job(
    jobName='import-my-model',
    importedModelName='my-custom-llama',
    roleArn='arn:aws:iam::123456789012:role/BedrockImportRole',
    modelDataSource={
        's3DataSource': {
            's3Uri': 's3://my-bucket/models/custom-llama/'
        }
    }
)