PARALLEL_ANALYSIS_WORKFLOW = {
    "Comment": "Parallel document analysis with multiple AI tasks",
    "StartAt": "ParallelAnalysis",
    "States": {
        "ParallelAnalysis": {
            "Type": "Parallel",
            "Branches": [
                {
                    "StartAt": "SentimentAnalysis",
                    "States": {
                        "SentimentAnalysis": {
                            "Type": "Task",
                            "Resource": "arn:aws:states:::bedrock:invokeModel",
                            "Parameters": {
                                "ModelId": "anthropic.claude-3-haiku-20240307-v1:0",
                                "Body": {
                                    "anthropic_version": "bedrock-2023-05-31",
                                    "max_tokens": 100,
                                    "messages": [{
                                        "role": "user",
                                        "content.$": "States.Format('Analyze sentiment (positive/negative/neutral) with confidence score. Text: {}', $.text)"
                                    }]
                                }
                            },
                            "ResultSelector": {
                                "analysis_type": "sentiment",
                                "result.$": "$.Body.content[0].text"
                            },
                            "End": True
                        }
                    }
                },
                {
                    "StartAt": "TopicClassification",
                    "States": {
                        "TopicClassification": {
                            "Type": "Task",
                            "Resource": "arn:aws:states:::bedrock:invokeModel",
                            "Parameters": {
                                "ModelId": "anthropic.claude-3-haiku-20240307-v1:0",
                                "Body": {
                                    "anthropic_version": "bedrock-2023-05-31",
                                    "max_tokens": 100,
                                    "messages": [{
                                        "role": "user",
                                        "content.$": "States.Format('Classify into one category: technology, business, health, entertainment, sports. Text: {}', $.text)"
                                    }]
                                }
                            },
                            "ResultSelector": {
                                "analysis_type": "topic",
                                "result.$": "$.Body.content[0].text"
                            },
                            "End": True
                        }
                    }
                },
                {
                    "StartAt": "EntityExtraction",
                    "States": {
                        "EntityExtraction": {
                            "Type": "Task",
                            "Resource": "arn:aws:states:::bedrock:invokeModel",
                            "Parameters": {
                                "ModelId": "anthropic.claude-3-haiku-20240307-v1:0",
                                "Body": {
                                    "anthropic_version": "bedrock-2023-05-31",
                                    "max_tokens": 200,
                                    "messages": [{
                                        "role": "user",
                                        "content.$": "States.Format('Extract named entities (people, organizations, locations) as JSON. Text: {}', $.text)"
                                    }]
                                }
                            },
                            "ResultSelector": {
                                "analysis_type": "entities",
                                "result.$": "$.Body.content[0].text"
                            },
                            "End": True
                        }
                    }
                }
            ],
            "ResultPath": "$.analyses",
            "Next": "CombineResults"
        },
        "CombineResults": {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke",
            "Parameters": {
                "FunctionName": "combine-analysis-results",
                "Payload.$": "$"
            },
            "End": True
        }
    }
}