import boto3
import json
import time
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')
bedrock_runtime = boto3.client('bedrock-runtime')

def check_model_health(model_id: str) -> dict:
    """
    Perform health check on a Bedrock model.
    """
    start_time = time.time()

    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hello"}]
            })
        )

        latency = (time.time() - start_time) * 1000  # ms
        result = json.loads(response['body'].read())

        return {
            'status': 'healthy',
            'latency_ms': latency,
            'model_id': model_id,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'model_id': model_id,
            'timestamp': datetime.utcnow().isoformat()
        }

def publish_health_metrics(health_result: dict):
    """Publish health check results to CloudWatch."""
    cloudwatch.put_metric_data(
        Namespace='GenAI/Bedrock',
        MetricData=[
            {
                'MetricName': 'ModelHealth',
                'Dimensions': [
                    {'Name': 'ModelId', 'Value': health_result['model_id']}
                ],
                'Value': 1 if health_result['status'] = 'healthy' else 0,
                'Unit': 'Count'
            },
            {
                'MetricName': 'InvokeLatency',
                'Dimensions': [
                    {'Name': 'ModelId', 'Value': health_result['model_id']}
                ],
                'Value': health_result.get('latency_ms', 0),
                'Unit': 'Milliseconds'
            }
        ]
    )

def setup_health_alarm(model_id: str):
    """Create CloudWatch alarm for model health."""
    cloudwatch.put_metric_alarm(
        AlarmName=f'bedrock-{model_id.replace(":", "-")}-health',
        MetricName='ModelHealth',
        Namespace='GenAI/Bedrock',
        Dimensions=[
            {'Name': 'ModelId', 'Value': model_id}
        ],
        Statistic='Average',
        Period`,
        EvaluationPeriods=3,
        Threshold=0.5,
        ComparisonOperator='LessThanThreshold',
        AlarmActions=[
            'arn:aws:sns:us-east-1:123456789012:bedrock-alerts'
        ],
        AlarmDescription=f'Model {model_id} health check failures'
    )

# Lambda handler for scheduled health checks
def lambda_health_check_handler(event, context):
    models = [
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-haiku-20240307-v1:0"
    ]

    results = []
    for model_id in models:
        health = check_model_health(model_id)
        publish_health_metrics(health)
        results.append(health)

    return {'health_checks': results}