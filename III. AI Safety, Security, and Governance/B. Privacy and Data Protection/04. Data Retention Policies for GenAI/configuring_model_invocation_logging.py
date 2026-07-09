import boto3

bedrock = boto3.client('bedrock')

def enable_s3_logging(bucket_name, kms_key_arn=None):
    """
    Enable model invocation logging to S3.
    """
    logging_config = {
        's3Config': {
            'bucketName': bucket_name,
            'keyPrefix': 'bedrock-logs/'
        },
        'textDataDeliveryEnabled': True,  # Log prompt/response text
        'imageDataDeliveryEnabled': True,  # Log image data
        'embeddingDataDeliveryEnabled': True  # Log embedding vectors
    }

    if kms_key_arn:
        logging_config['s3Config']['kmsKeyId'] = kms_key_arn

    response = bedrock.put_model_invocation_logging_configuration(
        loggingConfig=logging_config
    )
    return response

def enable_cloudwatch_logging(log_group_name):
    """
    Enable model invocation logging to CloudWatch.
    """
    logging_config = {
        'cloudWatchConfig': {
            'logGroupName': log_group_name,
            'roleArn': 'arn:aws:iam::123456789012:role/BedrockLoggingRole',
            'largeDataDeliveryS3Config': {
                'bucketName': 'overflow-bucket',  # For large responses
                'keyPrefix': 'large-data/'
            }
        },
        'textDataDeliveryEnabled': True,
        'imageDataDeliveryEnabled': False,  # Reduce log volume
        'embeddingDataDeliveryEnabled': False
    }

    response = bedrock.put_model_invocation_logging_configuration(
        loggingConfig=logging_config
    )
    return response

def disable_content_logging():
    """
    Enable metadata-only logging (no prompt/response content).
    """
    logging_config = {
        's3Config': {
            'bucketName': 'my-logs-bucket',
            'keyPrefix': 'metadata-logs/'
        },
        'textDataDeliveryEnabled': False,  # No text content
        'imageDataDeliveryEnabled': False,
        'embeddingDataDeliveryEnabled': False
    }

    response = bedrock.put_model_invocation_logging_configuration(
        loggingConfig=logging_config
    )
    return response

# Enable full logging to S3
enable_s3_logging(
    bucket_name='my-bedrock-logs',
    kms_key_arn='arn:aws:kms:us-east-1:123456789012:key/my-key'
)