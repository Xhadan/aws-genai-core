{
  "Statement": [
    {
      "Principal": "*",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:Converse"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-*"
      ]
    }
  ]
}