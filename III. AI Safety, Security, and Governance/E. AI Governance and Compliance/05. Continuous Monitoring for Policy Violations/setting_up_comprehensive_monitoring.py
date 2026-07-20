import boto3
import json
from datetime import datetime, timedelta

cloudwatch = boto3.client('cloudwatch')
logs = boto3.client('logs')
bedrock = boto3.client('bedrock')

def enable_model_invocation_logging(log_group_name, s3_bucket=None):
    """
    Enable Bedrock Model Invocation Logging.
    """
    logging_config = {
        'cloudWatchConfig': {
            'logGroupName': log_group_name,
            'roleArn': 'arn:aws:iam::123456789012:role/BedrockLoggingRole',
            'largeDataDeliveryS3Config': {
                's3BucketName': s3_bucket,
                's3KeyPrefix': 'bedrock-logs/large-payloads/'
            } if s3_bucket else None
        },
        'embeddingDataDeliveryEnabled': True,
        'imageDataDeliveryEnabled': True,
        'textDataDeliveryEnabled': True
    }

    # Remove None values
    if not s3_bucket:
        del logging_config['cloudWatchConfig']['largeDataDeliveryS3Config']

    response = bedrock.put_model_invocation_logging_configuration(
        loggingConfig=logging_config
    )

    print(f"Invocation logging enabled to: {log_group_name}")
    return response


def create_monitoring_dashboard(dashboard_name, model_id):
    """
    Create CloudWatch dashboard for GenAI monitoring.
    """
    widgets = [
        # Latency widget
        {
            'type': 'metric',
            'x': 0, 'y': 0, 'width': 12, 'height': 6,
            'properties': {
                'title': 'Model Invocation Latency',
                'metrics': [
                    ['AWS/Bedrock', 'InvocationLatency', 'ModelId', model_id, {'stat': 'p50', 'label': 'p50'}],
                    ['...', {'stat': 'p95', 'label': 'p95'}],
                    ['...', {'stat': 'p99', 'label': 'p99'}]
                ],
                'period': 60,
                'region': 'us-east-1'
            }
        },
        # Invocation count widget
        {
            'type': 'metric',
            'x': 12, 'y': 0, 'width': 12, 'height': 6,
            'properties': {
                'title': 'Invocation Count',
                'metrics': [
                    ['AWS/Bedrock', 'Invocations', 'ModelId', model_id],
                    ['AWS/Bedrock', 'InvocationClientErrors', 'ModelId', model_id],
                    ['AWS/Bedrock', 'InvocationServerErrors', 'ModelId', model_id]
                ],
                'period': 60,
                'stat': 'Sum'
            }
        },
        # Token usage widget
        {
            'type': 'metric',
            'x': 0, 'y': 6, 'width': 12, 'height': 6,
            'properties': {
                'title': 'Token Usage',
                'metrics': [
                    ['AWS/Bedrock', 'InputTokenCount', 'ModelId', model_id],
                    ['AWS/Bedrock', 'OutputTokenCount', 'ModelId', model_id]
                ],
                'period': 300,
                'stat': 'Sum'
            }
        },
        # Guardrail metrics widget
        {
            'type': 'metric',
            'x': 12, 'y': 6, 'width': 12, 'height': 6,
            'properties': {
                'title': 'Guardrail Activity',
                'metrics': [
                    ['Custom/GenAI', 'GuardrailTriggered', 'Application', 'MyApp'],
                    ['Custom/GenAI', 'ContentBlocked', 'Application', 'MyApp'],
                    ['Custom/GenAI', 'PIIDetected', 'Application', 'MyApp']
                ],
                'period': 300,
                'stat': 'Sum'
            }
        }
    ]

    response = cloudwatch.put_dashboard(
        DashboardNameshboard_name,
        DashboardBody=json.dumps({'widgets': widgets})
    )

    print(f"Dashboard created: {dashboard_name}")
    return response


def create_monitoring_alarms(model_id, sns_topic_arn):
    """
    Create CloudWatch alarms for critical metrics.
    """
    alarms = [
        # High latency alarm
        {
            'AlarmName': f'{model_id}-high-latency',
            'MetricName': 'InvocationLatency',
            'Namespace': 'AWS/Bedrock',
            'Statistic': 'p99',
            'Period': 300,
            'EvaluationPeriods': 2,
            'Threshold': 10000,  # 10 seconds
            'ComparisonOperator': 'GreaterThanThreshold',
            'Dimensions': [{'Name': 'ModelId', 'Value': model_id}],
            'AlarmActions': [sns_topic_arn],
            'AlarmDescription': 'P99 latency exceeds 10 seconds'
        },
        # High error rate alarm
        {
            'AlarmName': f'{model_id}-high-error-rate',
            'MetricName': 'InvocationServerErrors',
            'Namespace': 'AWS/Bedrock',
            'Statistic': 'Sum',
            'Period': 300,
            'EvaluationPeriods': 2,
            'Threshold': 10,
            'ComparisonOperator': 'GreaterThanThreshold',
            'Dimensions': [{'Name': 'ModelId', 'Value': model_id}],
            'AlarmActions': [sns_topic_arn],
            'AlarmDescription': 'Server errors exceed threshold'
        },
        # Cost anomaly alarm (custom metric)
        {
            'AlarmName': 'genai-cost-anomaly',
            'MetricName': 'EstimatedCost',
            'Namespace': 'Custom/GenAI',
            'Statistic': 'Sum',
            'Period': 3600,  # 1 hour
            'EvaluationPeriods': 1,
            'Threshold': 100,  # $100/hour
            'ComparisonOperator': 'GreaterThanThreshold',
            'AlarmActions': [sns_topic_arn],
            'AlarmDescription': 'Hourly GenAI cost exceeds $100'
        }
    ]

    for alarm in alarms:
        cloudwatch.put_metric_alarm(**alarm)
        print(f"Alarm created: {alarm['AlarmName']}")


def publish_custom_metrics(metrics_data):
    """
    Publish custom GenAI metrics to CloudWatch.
    """
    metric_data = []

    for metric in metrics_data:
        metric_data.append({
            'MetricName': metric['name'],
            'Value': metric['value'],
            'Unit': metric.get('unit', 'Count'),
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': 'Application', 'Value': metric.get('application', 'GenAI')},
                {'Name': 'Environment', 'Value': metric.get('environment', 'production')}
            ]
        })

    cloudwatch.put_metric_data(
        Namespace='Custom/GenAI',
        MetricData=metric_data
    )


# Example: Set up comprehensive monitoring
enable_model_invocation_logging(
    log_group_name='/aws/bedrock/model-invocations',
    s3_bucket='my-genai-logs-bucket'
)

create_monitoring_dashboard(
    dashboard_name='GenAI-Production-Dashboard',
    model_id='anthropic.claude-3-sonnet-20240229-v1:0'
)

create_monitoring_alarms(
    model_id='anthropic.claude-3-sonnet-20240229-v1:0',
    sns_topic_arn='arn:aws:sns:us-east-1:123456789012:genai-alerts'
)