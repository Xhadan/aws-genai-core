import json
import base64
import gzip
import boto3
from datetime import datetime

# Lambda function for processing Bedrock invocation logs

cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')

def lambda_handler(event, context):
    """
    Process CloudWatch Logs subscription filter events.
    Triggered by new Bedrock invocation log entries.
    """
    # Decode and decompress log data
    compressed_payload = base64.b64decode(event['awslogs']['data'])
    uncompressed_payload = gzip.decompress(compressed_payload)
    log_data = json.loads(uncompressed_payload)

    alerts = []
    metrics = []

    for log_event in log_data['logEvents']:
        record = json.loads(log_event['message'])

        # Extract key fields
        model_id = record.get('modelId', 'unknown')
        latency_ms = record.get('metadata', {}).get('latencyMs', 0)
        error_code = record.get('metadata', {}).get('errorCode', '')
        input_tokens = record.get('input', {}).get('inputTokenCount', 0)
        output_tokens = record.get('output', {}).get('outputTokenCount', 0)

        # Check for errors
        if error_code:
            alerts.append({
                'type': 'error',
                'model_id': model_id,
                'error_code': error_code,
                'message': record.get('metadata', {}).get('errorMessage', ''),
                'request_id': record.get('requestId', '')
            })

        # Check for high latency
        if latency_ms > 30000:  # 30 second threshold
            alerts.append({
                'type': 'high_latency',
                'model_id': model_id,
                'latency_ms': latency_ms,
                'request_id': record.get('requestId', '')
            })

        # Check for expensive prompts
        if input_tokens > 100000:
            alerts.append({
                'type': 'expensive_prompt',
                'model_id': model_id,
                'input_tokens': input_tokens,
                'request_id': record.get('requestId', '')
            })

        # Publish custom metrics
        metrics.append({
            'model_id': model_id,
            'latency_ms': latency_ms,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'has_error': 1 if error_code else 0
        })

    # Publish metrics to CloudWatch
    publish_metrics(metrics)

    # Send alerts if any
    if alerts:
        send_alerts(alerts)

    return {
        'statusCode': 200,
        'processed': len(log_data['logEvents']),
        'alerts': len(alerts)
    }


def publish_metrics(metrics):
    """Publish aggregated metrics to CloudWatch"""
    if not metrics:
        return

    metric_data = []

    for m in metrics:
        dimensions = [{'Name': 'ModelId', 'Value': m['model_id']}]

        metric_data.extend([
            {
                'MetricName': 'ProcessedInvocations',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': dimensions
            },
            {
                'MetricName': 'ProcessedLatency',
                'Value': m['latency_ms'],
                'Unit': 'Milliseconds',
                'Dimensions': dimensions
            }
        ])

    # CloudWatch limits to 1000 metrics per call
    for i in range(0, len(metric_data), 1000):
        batch = metric_data[i:i+1000]
        cloudwatch.put_metric_data(
            Namespace='GenAI/Logs/Processed',
            MetricDatatch
        )


def send_alerts(alerts):
    """Send alerts via SNS"""
    alert_topic_arn = 'arn:aws:sns:us-east-1:123456789012:bedrock-alerts'

    for alert in alerts:
        sns.publish(
            TopicArn=alert_topic_arn,
            Subject=f"Bedrock Alert: {alert['type']}",
            Message=json.dumps(alert, indent=2)
        )