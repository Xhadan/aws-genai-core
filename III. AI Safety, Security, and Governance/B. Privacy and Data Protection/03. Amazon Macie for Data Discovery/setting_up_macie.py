import boto3

macie = boto3.client('macie2')
s3 = boto3.client('s3')

def enable_macie():
    """Enable Macie for the account."""
    try:
        macie.enable_macie()
        print("Macie enabled successfully")
    except macie.exceptions.ConflictException:
        print("Macie already enabled")

def add_buckets_to_monitoring(bucket_names):
    """Add S3 buckets to Macie monitoring."""
    for bucket in bucket_names:
        # Macie automatically monitors all buckets
        # Use classification jobs for specific scanning
        print(f"Bucket {bucket} will be included in Macie inventory")

def create_sensitive_data_job(bucket_name, job_name):
    """Create a sensitive data discovery job."""
    response = macie.create_classification_job(
        name=job_name,
        description='Scan GenAI knowledge base for sensitive data',
        jobType='ONE_TIME',  # or 'SCHEDULED'
        s3JobDefinition={
            'bucketDefinitions': [
                {
                    'accountId': boto3.client('sts').get_caller_identity()['Account'],
                    'buckets': [bucket_name]
                }
            ],
            'scoping': {
                'includes': {
                    'and': [
                        {
                            'simpleScopeTerm': {
                                'comparator': 'STARTS_WITH',
                                'key': 'OBJECT_KEY',
                                'values': ['knowledge-base/', 'training-data/']
                            }
                        }
                    ]
                }
            }
        },
        # Include managed identifiers
        managedDataIdentifierSelector='ALL',
        # Sampling
        samplingPercentage0,  # Scan all objects
        tags={'Purpose': 'GenAI-Data-Security'}
    )

    return response['jobId']

# Setup
enable_macie()

# Create job for knowledge base bucket
job_id = create_sensitive_data_job(
    bucket_name='my-genai-knowledge-base',
    job_name='genai-kb-scan-2024'
)
print(f"Created job: {job_id}")