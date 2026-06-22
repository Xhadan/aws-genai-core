import json
import boto3
import os

bedrock_runtime = boto3.client('bedrock-runtime')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def document_processor_handler(event, context):
    """
    Lambda handler triggered by EventBridge when PDF uploaded to S3.
    Extracts text and generates AI summary.
    """
    print(f"Received event: {json.dumps(event)}")

    # Extract S3 info from EventBridge event
    detail = event.get('detail', {})
    bucket = detail.get('bucket', {}).get('name')
    key = detail.get('object', {}).get('key')

    if not bucket or not key:
        print("Missing bucket or key in event")
        return {'statusCode': 400}

    # Download document (simplified - real impl would use Textract)
    response = s3.get_object(Bucket=bucket, Key=key)
    document_text = extract_text_from_document(response['Body'].read())

    # Generate summary with Bedrock
    summary_response = bedrock_runtime.invoke_model(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{
                "role": "user",
                "content": f"Summarize this document in 3-5 bullet points:\n\n{document_text[:10000]}"
            }]
        })
    )

    result = json.loads(summary_response['body'].read())
    summary = result['content'][0]['text']

    # Store result
    results_table = dynamodb.Table(os.environ['RESULTS_TABLE'])
    results_table.put_item(Item={
        'document_key': f"{bucket}/{key}",
        'summary': summary,
        'processed_at': event.get('time'),
        'source_event_id': event.get('id')
    })

    # Emit completion event
    events = boto3.client('events')
    events.put_events(Entries=[{
        'Source': 'genai.document-processor',
        'DetailType': 'Document Processed',
        'Detail': json.dumps({
            'bucket': bucket,
            'key': key,
            'summary_length': len(summary),
            'status': 'completed'
        }),
        'EventBusName': 'genai-events'
    }])

    return {'statusCode': 200, 'summary_length': len(summary)}

def extract_text_from_document(content: bytes) -> str:
    """Extract text from document (placeholder - use Textract in production)."""
    # In production, use Amazon Textract for PDF extraction
    return content.decode('utf-8', errors='ignore')


# EventBridge Rule (CloudFormation/Terraform):
"""
EventBridgeRule:
  Type: AWS::Events::Rule
  Properties:
    Name: document-upload-rule
    EventBusName: default
    EventPattern:
      source:
        - aws.s3
      detail-type:
        - Object Created
      detail:
        bucket:
          name:
            - documents-bucket
        object:
          key:
            - suffix: .pdf
    Targets:
      - Id: document-processor
        Arn: !GetAtt DocumentProcessorFunction.Arn
"""