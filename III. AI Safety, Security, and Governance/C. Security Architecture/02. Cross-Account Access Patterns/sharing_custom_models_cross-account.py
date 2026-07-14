import boto3
import json

bedrock = boto3.client('bedrock')

def share_custom_model(model_id, consumer_account_ids):
    """
    Share a custom model with other AWS accounts.
    """
    # Build resource policy
    statements = []
    for account_id in consumer_account_ids:
        statements.append({
            "Sid": f"AllowAccount{account_id}",
            "Effect": "Allow",
            "Principal": {
                "AWS": f"arn:aws:iam::{account_id}:root"
            },
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:GetCustomModel"
            ],
            "Resource": f"arn:aws:bedrock:*:{boto3.client('sts').get_caller_identity()['Account']}:custom-model/{model_id}"
        })

    policy = {
        "Version": "2012-10-17",
        "Statement": statements
    }

    # Attach policy to model
    response = bedrock.put_model_resource_policy(
        modelIdentifier=model_id,
        resourcePolicy=json.dumps(policy)
    )

    print(f"Model {model_id} shared with accounts: {consumer_account_ids}")
    return response

# Share model with two accounts
share_custom_model(
    model_id='my-fine-tuned-model',
    consumer_account_ids=['111111111111', '222222222222']
)