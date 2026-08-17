import boto3
from datetime import datetime
from typing import Dict
import json

cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')

class BedrockErrorMonitor:
    """Monitor and alert on Bedrock errors."""

    def __init__(self, alarm_topic_arn: str):
        self.alarm_topic_arn = alarm_topic_arn
        self.error_counts = {}

    def log_error(
        self,
        error_code: str,
        model_id: str,
        request_id: str = None
    ):
        """Log error to CloudWatch."""

        # Publish metric
        cloudwatch.put_metric_data(
            Namespace='Bedrock/Errors',
            MetricData=[
                {
                    'MetricName': 'ErrorCount',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'ErrorCode', 'Value': error_code},
                        {'Name': 'ModelId', 'Value': model_id}
                    ],
                    'Timestamp': datetime.utcnow()
                }
            ]
        )

        # Track for alerting
        key = f"{error_code}:{model_id}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1

        # Alert on high error rates
        if self.error_counts[key] >= 10:
            self._send_alert(error_code, model_id, self.error_counts[key])
            self.error_counts[key] = 0

    def _send_alert(self, error_code: str, model_id: str, count: int):
        """Send alert via SNS."""

        message = {
            'alarm': 'BedrockHighErrorRate',
            'error_code': error_code,
            'model_id': model_id,
            'count': count,
            'timestamp': datetime.utcnow().isoformat()
        }

        sns.publish(
            TopicArn=self.alarm_topic_arn,
            Message=json.dumps(message),
            Subject=f'Bedrock Error Alert: {error_code}'
        )

    def create_cloudwatch_alarm(self, error_code: str, threshold: int = 10):
        """Create CloudWatch alarm for error type."""

        cloudwatch.put_metric_alarm(
            AlarmName=f'Bedrock-{error_code}-High',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=1,
            MetricName='ErrorCount',
            Namespace='Bedrock/Errors',
            Period`,
            Statistic='Sum',
            Threshold=threshold,
            ActionsEnabled=True,
            AlarmActions=[self.alarm_topic_arn],
            AlarmDescription=f'High {error_code} rate in Bedrock',
            Dimensions=[
                {'Name': 'ErrorCode', 'Value': error_code}
            ]
        )