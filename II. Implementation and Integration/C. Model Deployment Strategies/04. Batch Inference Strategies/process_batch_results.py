import boto3
import json

s3 = boto3.client('s3')

def parse_batch_results(output_s3_uri: str):
    """
    Parse results from Bedrock batch inference job.
    Output is JSONL format with original recordId preserved.
    """
    # Parse S3 URI
    bucket = output_s3_uri.replace("s3://", "").split("/")[0]
    prefix = "/".join(output_s3_uri.replace("s3://", "").split("/")[1:])

    # List output files
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    results = []

    for obj in response.get('Contents', []):
        if obj['Key'].endswith('.jsonl.out'):
            # Read file
            file_response = s3.get_object(Bucket=bucket, Key=obj['Key'])
            content = file_response['Body'].read().decode('utf-8')

            # Parse each line
            for line in content.strip().split('\n'):
                if line:
                    record = json.loads(line)
                    results.append({
                        'recordId': record['recordId'],
                        'status': record.get('status', 'unknown'),
                        'output': record.get('modelOutput', {}).get('content', [{}])[0].get('text', ''),
                        'error': record.get('error')
                    })

    return results

def process_batch_results(output_s3_uri: str):
    """Process and aggregate batch results."""
    results = parse_batch_results(output_s3_uri)

    successful = [r for r in results if r['status'] = 'success']
    failed = [r for r in results if r['status'] != 'success']

    print(f"Total records: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print("\nFailed records:")
        for r in failed[:5]:  # Show first 5 failures
            print(f"  {r['recordId']}: {r.get('error', 'Unknown error')}")

    return results

# Example
results = process_batch_results("s3://my-batch-bucket/batch-jobs/output/")
for result in results[:3]:
    print(f"\n{result['recordId']}:")
    print(f"  {result['output'][:200]}...")