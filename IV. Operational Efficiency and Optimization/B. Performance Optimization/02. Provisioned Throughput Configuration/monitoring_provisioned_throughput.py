import boto3
from datetime import datetime, timedelta
from typing import Dict, List

cloudwatch = boto3.client('cloudwatch')

class ProvisionedThroughputMonitor:
    """Monitor provisioned throughput utilization and performance"""

    def __init__(self, provisioned_model_arn: str):
        self.provisioned_model_arn = provisioned_model_arn
        self.cloudwatch = boto3.client('cloudwatch')

    def get_utilization_metrics(self, hours: int = 24) -> Dict:
        """Get utilization metrics for provisioned throughput"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # Get invocation count
        invocation_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Bedrock',
            MetricName='Invocations',
            Dimensions=[
                {'Name': 'ModelId', 'Value': self.provisioned_model_arn}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period600,
            Statistics=['Sum', 'Average']
        )

        # Get token counts
        input_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Bedrock',
            MetricName='InputTokenCount',
            Dimensions=[
                {'Name': 'ModelId', 'Value': self.provisioned_model_arn}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period600,
            Statistics=['Sum', 'Average']
        )

        output_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Bedrock',
            MetricName='OutputTokenCount',
            Dimensions=[
                {'Name': 'ModelId', 'Value': self.provisioned_model_arn}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period600,
            Statistics=['Sum', 'Average']
        )

        # Get latency
        latency_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Bedrock',
            MetricName='InvocationLatency',
            Dimensions=[
                {'Name': 'ModelId', 'Value': self.provisioned_model_arn}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period600,
            Statistics=['Average', 'Maximum', 'p99']
        )

        return {
            'period_hours': hours,
            'invocations': {
                'total': sum(dp['Sum'] for dp in invocation_response.get('Datapoints', [])),
                'avg_per_hour': sum(dp['Average'] for dp in invocation_response.get('Datapoints', [])) / max(len(invocation_response.get('Datapoints', [])), 1)
            },
            'tokens': {
                'input_total': sum(dp['Sum'] for dp in input_response.get('Datapoints', [])),
                'output_total': sum(dp['Sum'] for dp in output_response.get('Datapoints', []))
            },
            'latency_ms': {
                'avg': self._safe_avg([dp.get('Average', 0) for dp in latency_response.get('Datapoints', [])]),
                'max': max([dp.get('Maximum', 0) for dp in latency_response.get('Datapoints', [])], default=0)
            }
        }

    def _safe_avg(self, values: List[float]) -> float:
        return sum(values) / len(values) if values else 0

    def create_utilization_alarm(
        self,
        alarm_name: str,
        threshold_percent: float = 80,
        sns_topic_arn: str = None
    ):
        """Create CloudWatch alarm for high utilization"""

        alarm_config = {
            'AlarmName': alarm_name,
            'AlarmDescription': f'Provisioned throughput utilization above {threshold_percent}%',
            'MetricName': 'InputTokenCount',  # Use as proxy for utilization
            'Namespace': 'AWS/Bedrock',
            'Dimensions': [
                {'Name': 'ModelId', 'Value': self.provisioned_model_arn}
            ],
            'Statistic': 'Sum',
            'Period': 60,
            'EvaluationPeriods': 5,
            'Threshold': threshold_percent * 1000,  # Adjust based on MU capacity
            'ComparisonOperator': 'GreaterThanThreshold',
            'TreatMissingData': 'notBreaching'
        }

        if sns_topic_arn:
            alarm_config['AlarmActions'] = [sns_topic_arn]
            alarm_config['OKActions'] = [sns_topic_arn]

        self.cloudwatch.put_metric_alarm(**alarm_config)

        return f"Created alarm: {alarm_name}"

    def create_latency_alarm(
        self,
        alarm_name: str,
        threshold_ms: float = 5000,
        sns_topic_arn: str = None
    ):
        """Create alarm for high latency"""

        alarm_config = {
            'AlarmName': alarm_name,
            'AlarmDescription': f'Provisioned throughput latency above {threshold_ms}ms',
            'MetricName': 'InvocationLatency',
            'Namespace': 'AWS/Bedrock',
            'Dimensions': [
                {'Name': 'ModelId', 'Value': self.provisioned_model_arn}
            ],
            'ExtendedStatistic': 'p99',
            'Period': 300,
            'EvaluationPeriods': 3,
            'Threshold': threshold_ms,
            'ComparisonOperator': 'GreaterThanThreshold',
            'TreatMissingData': 'notBreaching'
        }

        if sns_topic_arn:
            alarm_config['AlarmActions'] = [sns_topic_arn]

        self.cloudwatch.put_metric_alarm(**alarm_config)

        return f"Created alarm: {alarm_name}"


class AutoScalingManager:
    """Manage auto-scaling for provisioned throughput"""

    def __init__(self, manager: 'ProvisionedThroughputManager'):
        self.manager = manager
        self.cloudwatch = boto3.client('cloudwatch')

    def evaluate_scaling_need(
        self,
        provisioned_model_id: str,
        current_mus: int,
        scale_up_threshold: float = 80,
        scale_down_threshold: float = 30
    ) -> Dict:
        """
        Evaluate if scaling is needed based on utilization.
        Note: Actual auto-scaling would require additional automation.
        """
        # Get recent utilization
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes)

        response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Bedrock',
            MetricName='InputTokenCount',
            Dimensions=[
                {'Name': 'ModelId', 'Value': provisioned_model_id}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period`,
            Statistics=['Sum']
        )

        if not response.get('Datapoints'):
            return {'action': 'none', 'reason': 'No data'}

        # Calculate average utilization
        avg_tokens_per_min = sum(
            dp['Sum'] for dp in response['Datapoints']
        ) / len(response['Datapoints'])

        # Estimate capacity (example: 100K tokens/min per MU)
        capacity_per_mu = 100000
        total_capacity = current_mus * capacity_per_mu
        utilization_percent = (avg_tokens_per_min / total_capacity) * 100

        if utilization_percent > scale_up_threshold:
            new_mus = int(current_mus * 1.5)
            return {
                'action': 'scale_up',
                'current_mus': current_mus,
                'recommended_mus': new_mus,
                'utilization_percent': utilization_percent
            }
        elif utilization_percent < scale_down_threshold:
            new_mus = max(1, int(current_mus * 0.7))
            return {
                'action': 'scale_down',
                'current_mus': current_mus,
                'recommended_mus': new_mus,
                'utilization_percent': utilization_percent
            }
        else:
            return {
                'action': 'none',
                'utilization_percent': utilization_percent
            }


# Example: Set up monitoring
monitor = ProvisionedThroughputMonitor(
    provisioned_model_arn='arn:aws:bedrock:us-east-1:123456789012:provisioned-model/abc123'
)

# Get metrics
metrics = monitor.get_utilization_metrics(hours$)
print(f"Total invocations: {metrics['invocations']['total']}")
print(f"Avg latency: {metrics['latency_ms']['avg']:.0f}ms")

# Create alarms
monitor.create_utilization_alarm(
    alarm_name='pt-high-utilization',
    threshold_percent,
    sns_topic_arn='arn:aws:sns:us-east-1:123456789012:bedrock-alerts'
)