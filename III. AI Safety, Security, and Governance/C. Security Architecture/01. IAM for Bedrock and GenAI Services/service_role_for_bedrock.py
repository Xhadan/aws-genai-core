import boto3
import json

iam = boto3.client('iam')

def create_bedrock_service_role():
    """
    Create service role for Bedrock to access S3 and other services.
    """
    # Trust policy allowing Bedrock to assume the role
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "aws:SourceAccount": "123456789012"
                    },
                    "ArnLike": {
                        "aws:SourceArn": "arn:aws:bedrock:*:123456789012:*"
                    }
                }
            }
        ]
    }

    # Create role
    role_response = iam.create_role(
        RoleName='BedrockServiceRole',
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description='Service role for Amazon Bedrock'
    )

    role_arn = role_response['Role']['Arn']

    # Permissions policy for S3 access
    s3_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "S3Access",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::my-bedrock-data",
                    "arn:aws:s3:::my-bedrock-data/*"
                ]
            },
            {
                "Sid": "KMSAccess",
                "Effect": "Allow",
                "Action": [
                    "kms:Decrypt",
                    "kms:GenerateDataKey"
                ],
                "Resource": "arn:aws:kms:*:123456789012:key/*",
                "Condition": {
                    "StringEquals": {
                        "kms:ViaService": "s3.us-east-1.amazonaws.com"
                    }
                }
            }
        ]
    }

    # Attach inline policy
    iam.put_role_policy(
        RoleName='BedrockServiceRole',
        PolicyName='BedrockS3Access',
        PolicyDocument=json.dumps(s3_policy)
    )

    return role_arn

role_arn = create_bedrock_service_role()
print(f"Service role created: {role_arn}")