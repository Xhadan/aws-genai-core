import boto3
import json
import time
from datetime import datetime

bedrock = boto3.client('bedrock')
s3 = boto3.client('s3')

class BatchInferenceManager:
    """Manage Bedrock batch inference jobs"""

    def __init__(self, bucket_name: str, role_arn: str):
        self.bucket_name = bucket_name
        self.role_arn = role_arn
        self.bedrock = boto3.client('bedrock')
        self.s3 = boto3.client('s3')

    def prepare_batch_input(
        self,
        prompts: list,
        model_id: str,
        prefix: str = 'batch-input'
    ) -> str:
        """
        Prepare batch input file in S3.

        Args:
            prompts: List of prompt strings or dicts with prompt and metadata
            model_id: Model to use for inference
            prefix: S3 key prefix

        Returns:
            S3 URI of input file
        """
        # Create JSONL content
        lines = []
        for i, prompt in enumerate(prompts):
            if isinstance(prompt, str):
                prompt_text = prompt
                metadata = {}
            else:
                prompt_text = prompt['text']
                metadata = prompt.get('metadata', {})

            record = {
                'recordId': str(i),
                'modelInput': {
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 1000,
                    'messages': [
                        {'role': 'user', 'content': prompt_text}
                    ]
                }
            }

            # Include metadata in recordId for tracking
            if metadata:
                record['recordId'] = json.dumps({'id': i, **metadata})

            lines.append(json.dumps(record))

        content = '\n'.join(lines)

        # Upload to S3
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        key = f"{prefix}/{timestamp}/input.jsonl"

        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content.encode('utf-8')
        )

        return f"s3://{self.bucket_name}/{key}"

    def create_batch_job(
        self,
        model_id: str,
        input_s3_uri: str,
        output_prefix: str = 'batch-output'
    ) -> str:
        """Create batch inference job"""

        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        job_name = f"batch-job-{timestamp}"
        output_s3_uri = f"s3://{self.bucket_name}/{output_prefix}/{timestamp}/"

        response = self.bedrock.create_model_invocation_job(
            jobName=job_name,
            modelId=model_id,
            roleArn=self.role_arn,
            inputDataConfig={
                's3InputDataConfig': {
                    's3Uri': input_s3_uri
                }
            },
            outputDataConfig={
                's3OutputDataConfig': {
                    's3Uri': output_s3_uri
                }
            }
        )

        return response['jobArn']

    def wait_for_job(
        self,
        job_arn: str,
        poll_interval: int = 60,
        max_wait: int = 86400
    ) -> dict:
        """Wait for batch job to complete"""
        start_time = time.time()

        while True:
            response = self.bedrock.get_model_invocation_job(
                jobIdentifier=job_arn
            )

            status = response['status']

            if status = 'Completed':
                return {
                    'status': 'Completed',
                    'output_uri': response['outputDataConfig']['s3OutputDataConfig']['s3Uri'],
                    'metrics': response.get('metrics', {})
                }
            elif status in ['Failed', 'Stopped']:
                return {
                    'status': status,
                    'error': response.get('message', 'Unknown error')
                }

            elapsed = time.time() - start_time
            if elapsed > max_wait:
                return {
                    'status': 'Timeout',
                    'error': f'Job did not complete within {max_wait} seconds'
                }

            print(f"Job status: {status}, elapsed: {elapsed:.0f}s")
            time.sleep(poll_interval)

    def get_results(self, output_s3_uri: str) -> list:
        """Retrieve and parse batch results from S3"""

        # Parse S3 URI
        bucket, prefix = output_s3_uri.replace('s3://', '').split('/', 1)

        # List output files
        response = self.s3.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
        )

        results = []

        for obj in response.get('Contents', []):
            if obj['Key'].endswith('.jsonl'):
                # Download and parse
                file_response = self.s3.get_object(
                    Bucket=bucket,
                    Key=obj['Key']
                )
                content = file_response['Body'].read().decode('utf-8')

                for line in content.strip().split('\n'):
                    if line:
                        result = json.loads(line)
                        results.append({
                            'record_id': result['recordId'],
                            'output': result.get('modelOutput', {}).get('content', [{}])[0].get('text', ''),
                            'usage': result.get('modelOutput', {}).get('usage', {}),
                            'error': result.get('error')
                        })

        return results


def batch_process_documents(
    documents: list,
    task_prompt: str,
    model_id: str = 'anthropic.claude-3-haiku-20240307-v1:0'
):
    """
    Process documents using batch inference.

    Args:
        documents: List of document texts to process
        task_prompt: Instruction for processing each document
        model_id: Model to use
    """
    manager = BatchInferenceManager(
        bucket_name='your-bucket',
        role_arn='arn:aws:iam::123456789012:role/BedrockBatchRole'
    )

    # Prepare prompts
    prompts = []
    for i, doc in enumerate(documents):
        prompts.append({
            'text': f"{task_prompt}\n\nDocument:\n{doc}",
            'metadata': {'doc_index': i}
        })

    # Create and run batch job
    input_uri = manager.prepare_batch_input(prompts, model_id)
    job_arn = manager.create_batch_job(model_id, input_uri)

    print(f"Created batch job: {job_arn}")

    # Wait for completion
    result = manager.wait_for_job(job_arn)

    if result['status'] = 'Completed':
        results = manager.get_results(result['output_uri'])
        return results
    else:
        raise Exception(f"Batch job failed: {result.get('error')}")


# Example usage
documents = [
    "Contract document 1 text...",
    "Contract document 2 text...",
    # ... hundreds or thousands of documents
]

results = batch_process_documents(
    documents=documents,
    task_prompt="Extract the following from this contract: parties, effective date, term, and key obligations."
)

for r in results[:5]:
    print(f"Document {r['record_id']}: {r['output'][:100]}...")