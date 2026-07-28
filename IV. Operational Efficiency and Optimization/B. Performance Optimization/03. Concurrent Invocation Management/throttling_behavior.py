try:
    response = bedrock.converse(...)
except ClientError as e:
    if e.response['Error']['Code'] = 'ThrottlingException':
        # Handle throttling