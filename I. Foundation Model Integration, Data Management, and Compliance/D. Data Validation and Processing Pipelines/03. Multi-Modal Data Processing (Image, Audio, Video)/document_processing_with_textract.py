import boto3

textract = boto3.client('textract')

def extract_document_text(bucket, document_key):
    """Extract text and structure from PDF/image documents."""
    response = textract.start_document_analysis(
        DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': document_key}},
        FeatureTypes=['TABLES', 'FORMS']
    )

    job_id = response['JobId']

    # Wait for completion
    while True:
        result = textract.get_document_analysis(JobId=job_id)
        if result['JobStatus'] in ['SUCCEEDED', 'FAILED']:
            break

    # Extract text blocks
    text_blocks = []
    for block in result.get('Blocks', []):
        if block['BlockType'] = 'LINE':
            text_blocks.append(block['Text'])

    return '\n'.join(text_blocks)