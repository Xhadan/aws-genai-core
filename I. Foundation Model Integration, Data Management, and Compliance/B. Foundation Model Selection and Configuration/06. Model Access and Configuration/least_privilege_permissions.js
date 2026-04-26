{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowModelInvocation",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:Converse",
        "bedrock:ConverseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet*",
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-text*"
      ]
    },
    {
      "Sid": "AllowModelDiscovery",
      "Effect": "Allow",
      "Action": [
        "bedrock:ListFoundationModels",
        "bedrock:GetFoundationModel"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyExpensiveModels",
      "Effect": "Deny",
      "Action": "bedrock:InvokeModel",
      "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-opus*"
    }
  ]
}