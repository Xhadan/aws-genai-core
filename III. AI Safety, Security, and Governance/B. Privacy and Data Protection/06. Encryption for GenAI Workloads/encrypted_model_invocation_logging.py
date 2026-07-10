import boto3

bedrock = boto3.client('bedrock')

def enable_encrypted_logging(s3_bucket, kms_key_arn):
    """
    Enable model invocation logging with KMS encryption.
    """
    response = bedrock.put_model_invocation_logging_configuration(
        loggingConfig={
            's3Config': {
                'bucketName': s3_bucket,
                'keyPrefix': 'invocation-logs/',
                'kmsKeyId': kms_key_arn  # Encrypt logs with CMK
            },
            'textDataDeliveryEnabled': True,
            'imageDataDeliveryEnabled': True,
            'embeddingDataDeliveryEnabled': True
        }
    )
    print("Encrypted logging configured")
    return response

# Enable logging with encryption
enable_encrypted_logging(
    s3_bucket='my-bedrock-logs',
    kms_key_arn='arn:aws:kms:us-east-1:123456789012:key/logs-encryption-key'
)