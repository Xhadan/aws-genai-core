import boto3
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import math

bedrock = boto3.client('bedrock')
s3 = boto3.client('s3')

def chunk_data(data: list, chunk_size: int):
    """Split data into chunks for parallel processing."""
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

def create_parallel_batch_jobs(
    all_prompts: list,
    bucket: str,
    job_prefix: str,
    model_id: str,
    role_arn: str,
    max_records_per_job: int = 10000
):
    """
    Split large dataset into multiple batch jobs for parallel processing.
    """
    jobs = []
    chunks = list(chunk_data(all_prompts, max_records_per_job))

    print(f"Creating {len(chunks)} batch jobs for {len(all_prompts)} records")

    for idx, chunk in enumerate(chunks):
        # Prepare input file
        input_key = f"{job_prefix}/input/chunk-{idx}.jsonl"
        jsonl_content = ""

        for record_idx, prompt in enumerate(chunk):
            record = {
                "recordId": f"chunk-{idx}-record-{record_idx}",
                "modelInput": {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}]
                }
            }
            jsonl_content += json.dumps(record) + "\n"

        s3.put_object(
            Bucket=bucket,
            Key=input_key,
            Body=jsonl_content.encode('utf-8')
        )

        # Create job
        response = bedrock.create_model_invocation_job(
            jobName=f"{job_prefix}-chunk-{idx}",
            modelId=model_id,
            roleArn=role_arn,
            inputDataConfig={
                "s3InputDataConfig": {
                    "s3Uri": f"s3://{bucket}/{input_key}",
                    "s3InputFormat": "JSONL"
                }
            },
            outputDataConfig={
                "s3OutputDataConfig": {
                    "s3Uri": f"s3://{bucket}/{job_prefix}/output/chunk-{idx}/"
                }
            }
        )

        jobs.append({
            'job_arn': response['jobArn'],
            'chunk_idx': idx,
            'record_count': len(chunk)
        })

    return jobs

def monitor_all_jobs(jobs: list, poll_interval: int = 60):
    """Monitor multiple batch jobs in parallel."""

    def check_job(job):
        while True:
            response = bedrock.get_model_invocation_job(
                jobIdentifier=job['job_arn']
            )
            status = response['status']

            if status in ['Completed', 'Failed', 'Stopped']:
                return {
                    'job_arn': job['job_arn'],
                    'chunk_idx': job['chunk_idx'],
                    'status': status,
                    'output_uri': response.get('outputDataConfig', {}).get('s3OutputDataConfig', {}).get('s3Uri')
                }

            time.sleep(poll_interval)

    results = []
    with ThreadPoolExecutor(max_workers) as executor:
        futures = {executor.submit(check_job, job): job for job in jobs}

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f"Job {result['chunk_idx']} completed with status: {result['status']}")

    return results