import boto3
import json

bedrock = boto3.client('bedrock')

# Create automatic evaluation job
response = bedrock.create_evaluation_job(
    jobName='model-quality-eval-001',
    jobDescription='Weekly model quality assessment',
    roleArn='arn:aws:iam::123456789012:role/BedrockEvalRole',

    # Model to evaluate
    evaluationConfig={
        'automated': {
            'datasetMetricConfigs': [
                {
                    'taskType': 'Summarization',
                    'dataset': {
                        's3Uri': 's3://my-bucket/eval-datasets/summarization-test.jsonl'
                    },
                    'metricNames': [
                        'Accuracy',
                        'Robustness',
                        'BERTScore'
                    ]
                }
            ]
        }
    },

    # Inference configuration
    inferenceConfig={
        'models': [
            {
                'bedrockModel': {
                    'modelIdentifier': 'anthropic.claude-3-sonnet-20240229-v1:0',
                    'inferenceParams': json.dumps({
                        'max_tokens': 1024,
                        'temperature': 0.1
                    })
                }
            }
        ]
    },

    # Output location
    outputDataConfig={
        's3Uri': 's3://my-bucket/eval-results/'
    }
)

job_arn = response['jobArn']
print(f"Evaluation job created: {job_arn}")