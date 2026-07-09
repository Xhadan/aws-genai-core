import boto3
import json

s3 = boto3.client('s3')

def configure_log_retention(bucket_name, retention_days, archive_days65):
    """
    Configure S3 lifecycle policy for log retention compliance.
    """
    lifecycle_config = {
        'Rules': [
            {
                'ID': 'bedrock-logs-retention',
                'Status': 'Enabled',
                'Filter': {
                    'Prefix': 'bedrock-logs/'
                },
                'Transitions': [
                    {
                        'Days': retention_days,
                        'StorageClass': 'STANDARD_IA'  # Infrequent access
                    },
                    {
                        'Days': archive_days,
                        'StorageClass': 'GLACIER'  # Long-term archive
                    }
                ],
                'Expiration': {
                    'Days': retention_days + archive_days + 365  # Delete after total period
                }
            },
            {
                # Separate rule for compliance-sensitive logs
                'ID': 'compliance-logs-7-year',
                'Status': 'Enabled',
                'Filter': {
                    'Prefix': 'bedrock-logs/compliance/'
                },
                'Transitions': [
                    {'Days': 90, 'StorageClass': 'STANDARD_IA'},
                    {'Days': 365, 'StorageClass': 'GLACIER'},
                    {'Days': 1825, 'StorageClass': 'DEEP_ARCHIVE'}  # 5 years
                ],
                'Expiration': {
                    'Days': 2555  # 7 years total retention
                }
            }
        ]
    }

    s3.put_bucket_lifecycle_configuration(
        Bucket=bucket_name,
        LifecycleConfiguration=lifecycle_config
    )
    print(f"Lifecycle policy configured for {bucket_name}")

def enable_object_lock(bucket_name, retention_days65):
    """
    Enable S3 Object Lock for immutable audit logs.
    Must be enabled at bucket creation time.
    """
    # Note: Object Lock must be enabled when creating the bucket
    # This sets the default retention policy
    s3.put_object_lock_configuration(
        Bucket=bucket_name,
        ObjectLockConfiguration={
            'ObjectLockEnabled': 'Enabled',
            'Rule': {
                'DefaultRetention': {
                    'Mode': 'GOVERNANCE',  # or 'COMPLIANCE' for strict
                    'Days': retention_days
                }
            }
        }
    )
    print(f"Object Lock enabled for {bucket_name}")

# Configure retention
configure_log_retention(
    bucket_name='my-bedrock-logs',
    retention_days,
    archive_days65
)