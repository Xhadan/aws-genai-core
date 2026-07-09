import boto3
import json

ec2 = boto3.client('ec2')

def apply_endpoint_policy(endpoint_id, policy):
    """
    Apply restrictive policy to VPC endpoint.
    """
    ec2.modify_vpc_endpoint(
        VpcEndpointId=endpoint_id,
        PolicyDocument=json.dumps(policy)
    )
    print(f"Policy applied to endpoint {endpoint_id}")

# Restrictive policy - only allow Claude models
claude_only_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowClaudeModelsOnly",
            "Principal": "*",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:Converse",
                "bedrock:ConverseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-*"
            ]
        },
        {
            "Sid": "AllowKnowledgeBase",
            "Principal": "*",
            "Effect": "Allow",
            "Action": [
                "bedrock:Retrieve",
                "bedrock:RetrieveAndGenerate"
            ],
            "Resource": "*"
        }
    ]
}

# Policy restricting to specific accounts
account_restricted_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowSpecificAccounts",
            "Principal": {
                "AWS": [
                    "arn:aws:iam::111111111111:root",
                    "arn:aws:iam::222222222222:root"
                ]
            },
            "Effect": "Allow",
            "Action": "bedrock:*",
            "Resource": "*"
        }
    ]
}

# Apply policy
apply_endpoint_policy('vpce-12345678', claude_only_policy)