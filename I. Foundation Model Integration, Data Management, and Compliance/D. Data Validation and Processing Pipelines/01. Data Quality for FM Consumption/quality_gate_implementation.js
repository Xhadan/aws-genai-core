{
  "StartAt": "ValidateData",
  "States": {
    "ValidateData": {
      "Type": "Task",
      "Resource": "arn:aws:glue:us-east-1:123456789012:job/data-quality-check",
      "Next": "CheckQualityResults"
    },
    "CheckQualityResults": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.qualityScore",
          "NumericGreaterThanEquals": 0.95,
          "Next": "ProceedWithTraining"
        }
      ],
      "Default": "NotifyQualityFailure"
    },
    "ProceedWithTraining": {
      "Type": "Task",
      "Resource": "arn:aws:sagemaker:us-east-1:123456789012:training-job/*",
      "End": true
    },
    "NotifyQualityFailure": {
      "Type": "Task",
      "Resource": "arn:aws:sns:us-east-1:123456789012:quality-alerts",
      "End": true
    }
  }
}