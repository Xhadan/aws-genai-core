import json

# Step Functions state machine definition
evaluation_workflow = {
    "Comment": "GenAI Model Evaluation Pipeline",
    "StartAt": "LoadDataset",
    "States": {
        "LoadDataset": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:LoadEvalDataset",
            "Next": "ParallelEvaluations",
            "Retry": [
                {
                    "ErrorEquals": ["States.TaskFailed"],
                    "IntervalSeconds": 5,
                    "MaxAttempts": 2
                }
            ]
        },
        "ParallelEvaluations": {
            "Type": "Parallel",
            "Branches": [
                {
                    "StartAt": "AccuracyEvaluation",
                    "States": {
                        "AccuracyEvaluation": {
                            "Type": "Task",
                            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:EvalAccuracy",
                            "End": True
                        }
                    }
                },
                {
                    "StartAt": "ToxicityEvaluation",
                    "States": {
                        "ToxicityEvaluation": {
                            "Type": "Task",
                            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:EvalToxicity",
                            "End": True
                        }
                    }
                },
                {
                    "StartAt": "RAGASEvaluation",
                    "States": {
                        "RAGASEvaluation": {
                            "Type": "Task",
                            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:EvalRAGAS",
                            "End": True
                        }
                    }
                }
            ],
            "Next": "AggregateResults"
        },
        "AggregateResults": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:AggregateEvalResults",
            "Next": "QualityGateCheck"
        },
        "QualityGateCheck": {
            "Type": "Choice",
            "Choices": [
                {
                    "Variable": "$.quality_gate_passed",
                    "BooleanEquals": True,
                    "Next": "StoreResultsAndNotifySuccess"
                }
            ],
            "Default": "NotifyFailure"
        },
        "StoreResultsAndNotifySuccess": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:StoreAndNotify",
            "Parameters": {
                "status": "PASSED",
                "results.$": "$.results"
            },
            "End": True
        },
        "NotifyFailure": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:NotifyFailure",
            "End": True
        }
    }
}