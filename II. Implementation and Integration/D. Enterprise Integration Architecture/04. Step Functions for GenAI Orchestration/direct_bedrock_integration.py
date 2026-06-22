# Step Functions State Machine Definition (Amazon States Language)
STATE_MACHINE_DEFINITION = {
    "Comment": "GenAI Document Processing Pipeline",
    "StartAt": "ExtractText",
    "States": {
        "ExtractText": {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke",
            "Parameters": {
                "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:extract-text",
                "Payload.$": "$"
            },
            "ResultPath": "$.extractedText",
            "Next": "GenerateSummary"
        },
        "GenerateSummary": {
            "Type": "Task",
            "Resource": "arn:aws:states:::bedrock:invokeModel",
            "Parameters": {
                "ModelId": "anthropic.claude-3-sonnet-20240229-v1:0",
                "Body": {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "user",
                            "content.$": "States.Format('Summarize this document in 3-5 bullet points:\n\n{}', $.extractedText.Payload.text)"
                        }
                    ]
                }
            },
            "ResultSelector": {
                "summary.$": "$.Body.content[0].text"
            },
            "ResultPath": "$.summary",
            "Retry": [
                {
                    "ErrorEquals": ["Bedrock.ThrottlingException"],
                    "IntervalSeconds": 5,
                    "MaxAttempts": 3,
                    "BackoffRate": 2
                }
            ],
            "Next": "ExtractKeywords"
        },
        "ExtractKeywords": {
            "Type": "Task",
            "Resource": "arn:aws:states:::bedrock:invokeModel",
            "Parameters": {
                "ModelId": "anthropic.claude-3-haiku-20240307-v1:0",
                "Body": {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 256,
                    "messages": [
                        {
                            "role": "user",
                            "content.$": "States.Format('Extract 5-10 keywords from this text. Return only the keywords as a comma-separated list:\n\n{}', $.extractedText.Payload.text)"
                        }
                    ]
                }
            },
            "ResultSelector": {
                "keywords.$": "$.Body.content[0].text"
            },
            "ResultPath": "$.keywords",
            "Next": "StoreResults"
        },
        "StoreResults": {
            "Type": "Task",
            "Resource": "arn:aws:states:::dynamodb:putItem",
            "Parameters": {
                "TableName": "document-analysis",
                "Item": {
                    "documentId": {"S.$": "$.documentId"},
                    "summary": {"S.$": "$.summary.summary"},
                    "keywords": {"S.$": "$.keywords.keywords"},
                    "processedAt": {"S.$": "$$.State.EnteredTime"}
                }
            },
            "End": True
        }
    }
}