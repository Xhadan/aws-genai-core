import boto3
import time

bedrock = boto3.client('bedrock')

def wait_for_evaluation(job_arn, max_wait_minutes`):
    """Wait for evaluation job to complete and return results."""

    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60

    while True:
        response = bedrock.get_evaluation_job(jobIdentifier=job_arn)
        status = response['status']

        print(f"Job status: {status}")

        if status = 'Completed':
            return response
        elif status in ['Failed', 'Stopped']:
            raise Exception(f"Evaluation job {status}: {response.get('failureMessages', 'Unknown error')}")

        if time.time() - start_time > max_wait_seconds:
            raise TimeoutError(f"Evaluation job did not complete within {max_wait_minutes} minutes")

        time.sleep(30)  # Check every 30 seconds

# Get completed job results
job_arn = 'arn:aws:bedrock:us-east-1:123456789012:evaluation-job/abc123'
result = wait_for_evaluation(job_arn)

# Access evaluation metrics
print("Evaluation Results:")
print(f"  Job Name: {result['jobName']}")
print(f"  Status: {result['status']}")
print(f"  Output Location: {result['outputDataConfig']['s3Uri']}")

# Download detailed results from S3
import json
s3 = boto3.client('s3')
bucket = 'my-bucket'
key = 'eval-results/evaluation-results.json'

obj = s3.get_object(Bucket=bucket, Key=key)
results = json.loads(obj['Body'].read().decode('utf-8'))

for metric in results['metrics']:
    print(f"  {metric['name']}: {metric['value']:.3f}")