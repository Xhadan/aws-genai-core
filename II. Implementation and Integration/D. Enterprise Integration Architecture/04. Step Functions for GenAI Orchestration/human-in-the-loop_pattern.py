HUMAN_APPROVAL_WORKFLOW = {
    "Comment": "Content generation with human review",
    "StartAt": "GenerateContent",
    "States": {
        "GenerateContent": {
            "Type": "Task",
            "Resource": "arn:aws:states:::bedrock:invokeModel",
            "Parameters": {
                "ModelId": "anthropic.claude-3-sonnet-20240229-v1:0",
                "Body": {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": [{
                        "role": "user",
                        "content.$": "$.prompt"
                    }]
                }
            },
            "ResultSelector": {
                "generatedContent.$": "$.Body.content[0].text"
            },
            "ResultPath": "$.generation",
            "Next": "RequestApproval"
        },
        "RequestApproval": {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
            "Parameters": {
                "FunctionName": "send-approval-request",
                "Payload": {
                    "content.$": "$.generation.generatedContent",
                    "requestId.$": "$.requestId",
                    "taskToken.$": "$$.Task.Token"
                }
            },
            "ResultPath": "$.approval",
            "TimeoutSeconds": 86400,  # 24 hour timeout
            "Catch": [
                {
                    "ErrorEquals": ["States.Timeout"],
                    "ResultPath": "$.error",
                    "Next": "HandleTimeout"
                }
            ],
            "Next": "CheckApproval"
        },
        "CheckApproval": {
            "Type": "Choice",
            "Choices": [
                {
                    "Variable": "$.approval.status",
                    "StringEquals": "approved",
                    "Next": "PublishContent"
                },
                {
                    "Variable": "$.approval.status",
                    "StringEquals": "rejected",
                    "Next": "HandleRejection"
                },
                {
                    "Variable": "$.approval.status",
                    "StringEquals": "revision_requested",
                    "Next": "ReviseContent"
                }
            ],
            "Default": "HandleRejection"
        },
        "ReviseContent": {
            "Type": "Task",
            "Resource": "arn:aws:states:::bedrock:invokeModel",
            "Parameters": {
                "ModelId": "anthropic.claude-3-sonnet-20240229-v1:0",
                "Body": {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": [{
                        "role": "user",
                        "content.$": "States.Format('Revise this content based on feedback:\n\nOriginal:\n{}\n\nFeedback:\n{}', $.generation.generatedContent, $.approval.feedback)"
                    }]
                }
            },
            "ResultSelector": {
                "generatedContent.$": "$.Body.content[0].text"
            },
            "ResultPath": "$.generation",
            "Next": "RequestApproval"
        },
        "PublishContent": {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke",
            "Parameters": {
                "FunctionName": "publish-content",
                "Payload.$": "$"
            },
            "End": True
        },
        "HandleRejection": {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke",
            "Parameters": {
                "FunctionName": "handle-rejection",
                "Payload.$": "$"
            },
            "End": True
        },
        "HandleTimeout": {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke",
            "Parameters": {
                "FunctionName": "handle-timeout",
                "Payload.$": "$"
            },
            "End": True
        }
    }
}