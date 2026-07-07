import boto3
import time

comprehend = boto3.client('comprehend')

def start_batch_pii_detection(
    input_s3_uri,
    output_s3_uri,
    data_access_role_arn,
    mode='ONLY_REDACTION'  # or 'ONLY_OFFSETS'
):
    """
    Start async PII detection job for batch processing.
    """
    response = comprehend.start_pii_entities_detection_job(
        InputDataConfig={
            'S3Uri': input_s3_uri,
            'InputFormat': 'ONE_DOC_PER_LINE'
        },
        OutputDataConfig={
            'S3Uri': output_s3_uri
        },
        Mode=mode,  # ONLY_REDACTION replaces PII with [PII_TYPE]
        RedactionConfig={
            'PiiEntityTypes': [
                'BANK_ACCOUNT_NUMBER', 'BANK_ROUTING',
                'CREDIT_DEBIT_NUMBER', 'CREDIT_DEBIT_CVV', 'CREDIT_DEBIT_EXPIRY',
                'PIN', 'SSN', 'PASSPORT_NUMBER', 'DRIVER_ID',
                'NAME', 'EMAIL', 'PHONE', 'ADDRESS'
            ],
            'MaskMode': 'REPLACE_WITH_PII_ENTITY_TYPE'  # or 'MASK' for asterisks
        },
        DataAccessRoleArnta_access_role_arn,
        LanguageCode='en',
        JobName=f'pii-detection-{int(time.time())}'
    )

    return response['JobId']

def wait_for_job(job_id):
    """Wait for batch job completion."""
    while True:
        response = comprehend.describe_pii_entities_detection_job(JobId=job_id)
        status = response['PiiEntitiesDetectionJobProperties']['JobStatus']

        if status = 'COMPLETED':
            return response['PiiEntitiesDetectionJobProperties']
        elif status in ['FAILED', 'STOPPED']:
            raise Exception(f"Job {job_id} failed with status: {status}")

        print(f"Job status: {status}, waiting...")
        time.sleep(30)

# Example usage
job_id = start_batch_pii_detection(
    input_s3_uri='s3://my-bucket/input-documents/',
    output_s3_uri='s3://my-bucket/pii-output/',
    data_access_role_arn='arn:aws:iam::123456789012:role/ComprehendRole'
)

print(f"Started job: {job_id}")
result = wait_for_job(job_id)
print(f"Output location: {result['OutputDataConfig']['S3Uri']}")