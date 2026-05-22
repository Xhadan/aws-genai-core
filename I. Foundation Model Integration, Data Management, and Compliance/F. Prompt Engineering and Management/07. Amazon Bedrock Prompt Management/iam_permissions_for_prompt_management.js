{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PromptReadAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:GetPrompt",
        "bedrock:ListPrompts"
      ],
      "Resource": "arn:aws:bedrock:*:*:prompt/*"
    },
    {
      "Sid": "PromptWriteAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:CreatePrompt",
        "bedrock:UpdatePrompt",
        "bedrock:DeletePrompt"
      ],
      "Resource": "arn:aws:bedrock:*:*:prompt/*",
      "Condition": {
        "StringEquals": {
          "aws:RequestTag/Environment": "development"
        }
      }
    },
    {
      "Sid": "PromptInvocationAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock-agent-runtime:InvokeAgent"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ProductionPromptReadOnly",
      "Effect": "Allow",
      "Action": [
        "bedrock:GetPrompt"
      ],
      "Resource": "arn:aws:bedrock:*:*:prompt/*",
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/Environment": "production"
        }
      }
    }
  ]
}