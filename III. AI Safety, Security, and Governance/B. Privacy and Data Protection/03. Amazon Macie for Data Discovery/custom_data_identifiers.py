import boto3

macie = boto3.client('macie2')

def create_custom_identifier(name, description, regex_pattern, keywords=None):
    """
    Create custom data identifier for domain-specific sensitive data.
    """
    params = {
        'name': name,
        'description': description,
        'regex': regex_pattern,
        'severityLevels': [
            {'occurrencesThreshold': 1, 'severity': 'HIGH'}
        ]
    }

    if keywords:
        params['keywords'] = keywords
        params['maximumMatchDistance'] = 50  # Characters from keyword

    response = macie.create_custom_data_identifier(**params)
    return response['customDataIdentifierId']

# Create identifiers for internal sensitive data
identifiers = []

# Internal employee IDs
emp_id = create_custom_identifier(
    name='Internal-Employee-ID',
    description='Employee IDs in format EMP######',
    regex_pattern=r'EMP\d{6}',
    keywords=['employee', 'emp id', 'staff']
)
identifiers.append(emp_id)

# Internal project codes
project_code = create_custom_identifier(
    name='Confidential-Project-Code',
    description='Project codes for confidential projects',
    regex_pattern=r'PROJ-[A-Z]{3}-\d{4}',
    keywords=['project', 'code', 'initiative']
)
identifiers.append(project_code)

# Customer account numbers
account_num = create_custom_identifier(
    name='Customer-Account-Number',
    description='Internal customer account format',
    regex_pattern=r'ACCT-[A-Z]{2}\d{8}',
    keywords=['account', 'customer', 'client']
)
identifiers.append(account_num)

print(f"Created {len(identifiers)} custom identifiers")

def create_job_with_custom_identifiers(bucket_name, custom_ids):
    """Create job using custom identifiers."""
    response = macie.create_classification_job(
        name='custom-pii-scan',
        jobType='ONE_TIME',
        s3JobDefinition={
            'bucketDefinitions': [
                {
                    'accountId': boto3.client('sts').get_caller_identity()['Account'],
                    'buckets': [bucket_name]
                }
            ]
        },
        customDataIdentifierIds=custom_ids,
        managedDataIdentifierSelector='ALL'  # Also include AWS patterns
    )
    return response['jobId']