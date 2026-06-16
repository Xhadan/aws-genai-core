import boto3
import json
import time
from datetime import datetime

bedrock = boto3.client('bedrock')
s3 = boto3.client('s3')

def prepare_batch_input(
    prompts: list,
    bucket: str,
    input_key: str
):
    """
    Prepare JSONL input file for Bedrock batch inference.
    Each line is a complete inference request.
    """
    jsonl_content = ""

    for idx, prompt in enumerate(prompts):
        record = {
            "recordId": f"record-{idx}",
            "modelInput": {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        }
        jsonl_content += json.dumps(record) + "\n"

    # Upload to S3
    s3.put_object(
        Bucket=bucket,
        Key=input_key,
        Body=jsonl_content.encode('utf-8')
    )

    return f"s3://{bucket}/{input_key}"

def create_batch_inference_job(
    job_name: str,
    model_id: str,
    input_s3_uri: str,
    output_s3_uri: str,
    role_arn: str
):
    """
    Create a Bedrock batch inference job.
    """
    response = bedrock.create_model_invocation_job(
        jobName=job_name,
        modelId=model_id,
        roleArn=role_arn,
        inputDataConfig={
            "s3InputDataConfig": {
                "s3Uri": input_s3_uri,
                "s3InputFormat": "JSONL"
            }
        },
        outputDataConfig={
            "s3OutputDataConfig": {
                "s3Uri": output_s3_uri
            }
        },
        tags=[
            {"key": "Project", "value": "BatchProcessing"},
            {"key": "Environment", "value": "Production"}
        ]
    )

    job_arn = response['jobArn']
    print(f"Created batch job: {job_arn}")
    return job_arn

def monitor_batch_job(job_arn: str, poll_interval: int = 60):
    """Monitor batch job until completion."""

    while True:
        response = bedrock.get_model_invocation_job(jobIdentifier=job_arn)
        status = response['status']

        print(f"Job status: {status}")

        if status = 'Completed':
            print(f"Job completed successfully")
            print(f"Output: {response['outputDataConfig']['s3OutputDataConfig']['s3Uri']}")
            return response

        elif status = 'Failed':
            print(f"Job failed: {response.get('message', 'Unknown error')}")
            raise Exception(f"Batch job failed: {response.get('message')}")

        elif status in ['Stopping', 'Stopped']:
            print(f"Job was stopped")
            return response

        time.sleep(poll_interval)

# Example usage
prompts = [
    "Summarize the benefits of cloud computing.",
    "Explain machine learning in simple terms.",
    "What are the key features of serverless architecture?"
]

input_uri = prepare_batch_input(
    prompts=prompts,
    bucket="my-batch-bucket",
    input_key="batch-jobs/input/job-001.jsonl"
)

job_arn = create_batch_inference_job(
    job_name=f"batch-job-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    input_s3_uri=input_uri,
    output_s3_uri="s3://my-batch-bucket/batch-jobs/output/",
    role_arn="arn:aws:iam::123456789012:role/BedrockBatchRole"
)

result = monitor_batch_job(job_arn)