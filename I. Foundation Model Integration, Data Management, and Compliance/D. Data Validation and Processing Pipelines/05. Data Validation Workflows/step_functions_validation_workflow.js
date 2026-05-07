{
  "Comment": "GenAI Data Validation Pipeline",
  "StartAt": "ValidateSchema",
  "States": {
    "ValidateSchema": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:validate-schema",
      "Next": "CheckSchemaResult",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "Next": "HandleValidationError"
      }]
    },
    "CheckSchemaResult": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.schemaValid",
          "BooleanEquals": true,
          "Next": "RunQualityChecks"
        }
      ],
      "Default": "QuarantineData"
    },
    "RunQualityChecks": {
      "Type": "Task",
      "Resource": "arn:aws:states:::glue:startJobRun.sync",
      "Parameters": {
        "JobName": "data-quality-check",
        "Arguments": {
          "--input_path.$": "$.inputPath"
        }
      },
      "Next": "EvaluateQuality"
    },
    "EvaluateQuality": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.qualityScore",
          "NumericGreaterThanEquals": 0.95,
          "Next": "ApproveData"
        }
      ],
      "Default": "QuarantineData"
    },
    "ApproveData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:move-to-approved",
      "End": true
    },
    "QuarantineData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:quarantine-data",
      "Next": "NotifyFailure"
    },
    "NotifyFailure": {
      "Type": "Task",
      "Resource": "arn:aws:sns:us-east-1:123456789012:validation-alerts",
      "End": true
    },
    "HandleValidationError": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:handle-error",
      "End": true
    }
  }
}