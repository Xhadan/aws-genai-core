import boto3
import json

kms = boto3.client('kms')
iam = boto3.client('iam')

def create_bedrock_kms_key(alias_name='alias/bedrock-encryption'):
    """
    Create KMS key with policy allowing Bedrock service access.
    """
    account_id = boto3.client('sts').get_caller_identity()['Account']

    # Key policy allowing Bedrock and administrators
    key_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "Enable IAM User Permissions",
                "Effect": "Allow",
                "Principal": {"AWS": f"arn:aws:iam::{account_id}:root"},
                "Action": "kms:*",
                "Resource": "*"
            },
            {
                "Sid": "Allow Bedrock Service",
                "Effect": "Allow",
                "Principal": {"Service": "bedrock.amazonaws.com"},
                "Action": [
                    "kms:Decrypt",
                    "kms:GenerateDataKey",
                    "kms:GenerateDataKeyWithoutPlaintext",
                    "kms:DescribeKey",
                    "kms:CreateGrant"
                ],
                "Resource": "*",
                "Condition": {
                    "StringEquals": {
                        "aws:SourceAccount": account_id
                    }
                }
            },
            {
                "Sid": "Allow S3 Service for Logs",
                "Effect": "Allow",
                "Principal": {"Service": "s3.amazonaws.com"},
                "Action": [
                    "kms:Decrypt",
                    "kms:GenerateDataKey"
                ],
                "Resource": "*"
            }
        ]
    }

    # Create the key
    response = kms.create_key(
        Description='KMS key for Amazon Bedrock encryption',
        KeyUsage='ENCRYPT_DECRYPT',
        CustomerMasterKeySpec='SYMMETRIC_DEFAULT',
        Policy=json.dumps(key_policy),
        Tags=[
            {'TagKey': 'Purpose', 'TagValue': 'Bedrock-Encryption'},
            {'TagKey': 'Service', 'TagValue': 'GenAI'}
        ]
    )

    key_id = response['KeyMetadata']['KeyId']
    key_arn = response['KeyMetadata']['Arn']

    # Create alias
    kms.create_alias(
        AliasName=alias_name,
        TargetKeyId=key_id
    )

    # Enable automatic rotation
    kms.enable_key_rotation(KeyId=key_id)

    print(f"Created KMS key: {key_id}")
    print(f"ARN: {key_arn}")
    print(f"Alias: {alias_name}")

    return key_arn

# Create key
bedrock_key_arn = create_bedrock_kms_key()