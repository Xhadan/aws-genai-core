import boto3
import time

agentcore = boto3.client('bedrock-agentcore')

# Start a long-running agent task asynchronously
response = agentcore.start_agent_execution(
    endpointName='research-agent',
    executionConfig={
        'maxDurationSeconds': 28800,  # 8 hours
        'asyncMode': True
    },
    inputText='''
    Analyze the following 500 documents for compliance issues.
    Generate a comprehensive report with findings and recommendations.
    ''',
    inputData={
        's3InputPath': 's3://my-bucket/documents/batch-001/'
    }
)

execution_id = response['executionId']
print(f"Started execution: {execution_id}")

# Poll for completion (or use EventBridge for notifications)
while True:
    status = agentcore.get_agent_execution(
        endpointName='research-agent',
        executionId=execution_id
    )

    if status['status'] in ['COMPLETED', 'FAILED']:
        break

    print(f"Status: {status['status']} - Progress: {status.get('progress', 'N/A')}")
    time.sleep(60)

# Retrieve results
if status['status'] = 'COMPLETED':
    results = agentcore.get_agent_execution_output(
        endpointName='research-agent',
        executionId=execution_id
    )
    print(f"Report location: {results['s3OutputPath']}")