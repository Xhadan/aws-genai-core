BATCH_PROCESSING_WORKFLOW = {
    "Comment": "Process array of documents with Map state",
    "StartAt": "GetDocuments",
    "States": {
        "GetDocuments": {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke",
            "Parameters": {
                "FunctionName": "list-pending-documents",
                "Payload": {
                    "batch_size": 100
                }
            },
            "ResultPath": "$.documents",
            "Next": "ProcessDocuments"
        },
        "ProcessDocuments": {
            "Type": "Map",
            "ItemsPath": "$.documents.Payload",
            "MaxConcurrency": 10,  # Control parallelism
            "ItemSelector": {
                "documentId.$": "$$.Map.Item.Value.id",
                "content.$": "$$.Map.Item.Value.content",
                "index.$": "$$.Map.Item.Index"
            },
            "ItemProcessor": {
                "ProcessorConfig": {
                    "Mode": "INLINE"
                },
                "StartAt": "AnalyzeDocument",
                "States": {
                    "AnalyzeDocument": {
                        "Type": "Task",
                        "Resource": "arn:aws:states:::bedrock:invokeModel",
                        "Parameters": {
                            "ModelId": "anthropic.claude-3-sonnet-20240229-v1:0",
                            "Body": {
                                "anthropic_version": "bedrock-2023-05-31",
                                "max_tokens": 500,
                                "messages": [{
                                    "role": "user",
                                    "content.$": "States.Format('Analyze this document and provide: 1) Summary 2) Key points 3) Action items\n\nDocument:\n{}', $.content)"
                                }]
                            }
                        },
                        "ResultSelector": {
                            "documentId.$": "$.documentId",
                            "analysis.$": "$.Body.content[0].text"
                        },
                        "Retry": [
                            {
                                "ErrorEquals": ["Bedrock.ThrottlingException"],
                                "IntervalSeconds": 2,
                                "MaxAttempts": 5,
                                "BackoffRate": 2
                            }
                        ],
                        "Catch": [
                            {
                                "ErrorEquals": ["States.ALL"],
                                "ResultPath": "$.error",
                                "Next": "HandleError"
                            }
                        ],
                        "Next": "SaveResult"
                    },
                    "HandleError": {
                        "Type": "Pass",
                        "Result": {
                            "status": "failed"
                        },
                        "ResultPath": "$.processingResult",
                        "End": True
                    },
                    "SaveResult": {
                        "Type": "Task",
                        "Resource": "arn:aws:states:::dynamodb:putItem",
                        "Parameters": {
                            "TableName": "document-results",
                            "Item": {
                                "documentId": {"S.$": "$.documentId"},
                                "analysis": {"S.$": "$.analysis"}
                            }
                        },
                        "End": True
                    }
                }
            },
            "ResultPath": "$.processedDocuments",
            "Next": "GenerateBatchReport"
        },
        "GenerateBatchReport": {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke",
            "Parameters": {
                "FunctionName": "generate-batch-report",
                "Payload.$": "$"
            },
            "End": True
        }
    }
}