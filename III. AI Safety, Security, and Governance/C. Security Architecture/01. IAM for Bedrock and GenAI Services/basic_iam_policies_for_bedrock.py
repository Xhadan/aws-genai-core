import boto3
import json

iam = boto3.client('iam')

# Policy for application developers - invoke models only
developer_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "InvokeModels",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:Converse",
                "bedrock:ConverseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
                "arn:aws:bedrock:*::foundation-model/amazon.titan-*"
            ]
        },
        {
            "Sid": "ApplyGuardrails",
            "Effect": "Allow",
            "Action": "bedrock:ApplyGuardrail",
            "Resource": "arn:aws:bedrock:*:*:guardrail/*"
        },
        {
            "Sid": "QueryKnowledgeBases",
            "Effect": "Allow",
            "Action": [
                "bedrock:Retrieve",
                "bedrock:RetrieveAndGenerate"
            ],
            "Resource": "arn:aws:bedrock:*:*:knowledge-base/*"
        }
    ]
}

# Policy for ML engineers - includes custom model creation
ml_engineer_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "InvokeAndCustomize",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:Converse",
                "bedrock:ConverseStream",
                "bedrock:CreateModelCustomizationJob",
                "bedrock:GetModelCustomizationJob",
                "bedrock:ListModelCustomizationJobs",
                "bedrock:StopModelCustomizationJob"
            ],
            "Resource": "*"
        },
        {
            "Sid": "ManageCustomModels",
            "Effect": "Allow",
            "Action": [
                "bedrock:GetCustomModel",
                "bedrock:ListCustomModels",
                "bedrock:DeleteCustomModel"
            ],
            "Resource": "arn:aws:bedrock:*:*:custom-model/*"
        }
    ]
}

# Policy for platform administrators - full access
admin_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "BedrockFullAccess",
            "Effect": "Allow",
            "Action": [
                "bedrock:*"
            ],
            "Resource": "*"
        }
    ]
}

def create_policy(policy_name, policy_document, description):
    """Create IAM policy."""
    response = iam.create_policy(
        PolicyName=policy_name,
        PolicyDocument=json.dumps(policy_document),
        Descriptionscription
    )
    return response['Policy']['Arn']

# Create policies
dev_policy_arn = create_policy(
    'BedrockDeveloperAccess',
    developer_policy,
    'Allows model invocation and knowledge base queries'
)
print(f"Developer policy: {dev_policy_arn}")