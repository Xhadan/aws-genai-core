import boto3

logs = boto3.client('logs')

def set_log_retention(log_group_name, retention_days):
    """
    Set retention period for CloudWatch log group.
    Valid values: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    """
    logs.put_retention_policy(
        logGroupName=log_group_name,
        retentionInDays=retention_days
    )
    print(f"Retention set to {retention_days} days for {log_group_name}")

def create_log_group_with_retention(log_group_name, retention_days, kms_key_arn=None):
    """
    Create log group with retention and encryption.
    """
    # Create log group
    params = {'logGroupName': log_group_name}
    if kms_key_arn:
        params['kmsKeyId'] = kms_key_arn

    try:
        logs.create_log_group(**params)
    except logs.exceptions.ResourceAlreadyExistsException:
        print(f"Log group {log_group_name} already exists")

    # Set retention
    logs.put_retention_policy(
        logGroupName=log_group_name,
        retentionInDays=retention_days
    )

    print(f"Created {log_group_name} with {retention_days} day retention")

# Create log group for Bedrock with 90-day retention
create_log_group_with_retention(
    log_group_name='/aws/bedrock/model-invocations',
    retention_days,
    kms_key_arn='arn:aws:kms:us-east-1:123456789012:key/log-encryption-key'
)