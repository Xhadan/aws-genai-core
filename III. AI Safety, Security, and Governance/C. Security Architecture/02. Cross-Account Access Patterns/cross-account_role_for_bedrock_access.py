import boto3
import json

# In PROVIDER account
iam = boto3.client('iam')

def create_cross_account_role(role_name, consumer_account_id, allowed_models):
    """
    Create IAM role allowing consumer account to access Bedrock.
    """
    # Trust policy allowing consumer to assume role
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "AWS": f"arn:aws:iam::{consumer_account_id}:root"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "sts:ExternalId": "bedrock-access-external-id"  # For security
                }
            }
        }]
    }

    # Create role
    iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description='Cross-account role for Bedrock access'
    )

    # Permission policy
    resource_arns = [f"arn:aws:bedrock:*:*:custom-model/{m}" for m in allowed_models]
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:Converse"
            ],
            "Resource": resource_arns
        }]
    }

    iam.put_role_policy(
        RoleName=role_name,
        PolicyName='BedrockAccessPolicy',
        PolicyDocument=json.dumps(permissions_policy)
    )

    role_arn = f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}:role/{role_name}"
    print(f"Created role: {role_arn}")
    return role_arn

# Create role for consumer
role_arn = create_cross_account_role(
    role_name='BedrockCrossAccountAccess',
    consumer_account_id='111111111111',
    allowed_models=['model-1', 'model-2']
)