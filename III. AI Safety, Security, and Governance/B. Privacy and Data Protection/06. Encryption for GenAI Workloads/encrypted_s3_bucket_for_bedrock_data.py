import boto3
import json

s3 = boto3.client('s3')

def create_encrypted_bucket(bucket_name, kms_key_arn, region='us-east-1'):
    """
    Create S3 bucket with KMS encryption for Bedrock data.
    """
    # Create bucket
    if region = 'us-east-1':
        s3.create_bucket(Bucket=bucket_name)
    else:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': region}
        )

    # Enable default encryption with KMS
    s3.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            'Rules': [
                {
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'aws:kms',
                        'KMSMasterKeyID': kms_key_arn
                    },
                    'BucketKeyEnabled': True  # Reduces KMS API calls
                }
            ]
        }
    )

    # Block public access
    s3.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
        }
    )

    # Enforce encryption in transit
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "EnforceHTTPS",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ],
                "Condition": {
                    "Bool": {"aws:SecureTransport": "false"}
                }
            }
        ]
    }

    s3.put_bucket_policy(
        Bucket=bucket_name,
        Policy=json.dumps(bucket_policy)
    )

    print(f"Created encrypted bucket: {bucket_name}")
    return bucket_name

# Create bucket for knowledge base documents
create_encrypted_bucket(
    bucket_name='my-bedrock-knowledge-base',
    kms_key_arn='arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012'
)

# Create bucket for model invocation logs
create_encrypted_bucket(
    bucket_name='my-bedrock-logs',
    kms_key_arn='arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012'
)