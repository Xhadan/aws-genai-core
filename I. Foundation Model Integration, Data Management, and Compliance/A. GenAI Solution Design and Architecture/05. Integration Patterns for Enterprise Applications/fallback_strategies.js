{
  "InvokeBedrock": {
    "Type": "Task",
    "Resource": "arn:aws:states:::bedrock:invokeModel",
    "Parameters": {
      "ModelId": "anthropic.claude-3-sonnet-20240229-v1:0",
      "Body": {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [{"role": "user", "content.$": "$.prompt"}],
        "max_tokens": 1024
      }
    },
    "Retry": [
      {
        "ErrorEquals": ["Bedrock.ThrottlingException"],
        "IntervalSeconds": 2,
        "MaxAttempts": 3,
        "BackoffRate": 2
      }
    ],
    "Catch": [
      {
        "ErrorEquals": ["States.ALL"],
        "Next": "FallbackModel"
      }
    ],
    "Next": "ProcessResponse"
  },
  "FallbackModel": {
    "Type": "Task",
    "Resource": "arn:aws:states:::bedrock:invokeModel",
    "Parameters": {
      "ModelId": "anthropic.claude-3-haiku-20240307-v1:0",
      "Body": {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [{"role": "user", "content.$": "$.prompt"}],
        "max_tokens": 512
      }
    },
    "Next": "ProcessResponse"
  }
}