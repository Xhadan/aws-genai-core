import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

cloudwatch = boto3.client('cloudwatch')

class BedrockMonitoringSetup:
    """Set up comprehensive CloudWatch monitoring for Bedrock"""

    def __init__(self, model_id: str, alarm_topic_arn: str = None):
        self.cloudwatch = boto3.client('cloudwatch')
        self.model_id = model_id
        self.alarm_topic_arn = alarm_topic_arn
        self.namespace = 'AWS/Bedrock'

    def get_metrics(
        self,
        metric_names: List[str],
        start_time: datetime,
        end_time: datetime,
        period: int = 300,
        statistics: List[str] = None
    ) -> Dict[str, List]:
        """Get multiple metrics in single call"""
        statistics = statistics or ['Sum', 'Average', 'Maximum']

        results = {}
        for metric_name in metric_names:
            response = self.cloudwatch.get_metric_statistics(
                Namespace=self.namespace,
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'ModelId', 'Value': self.model_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=statistics
            )
            results[metric_name] = response.get('Datapoints', [])

        return results

    def create_error_rate_alarm(
        self,
        alarm_name: str,
        threshold_percent: float = 5.0,
        evaluation_periods: int = 3
    ):
        """Create alarm for high error rate"""

        # Use metric math to calculate error rate
        self.cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription=f'Bedrock error rate exceeds {threshold_percent}%',
            Metrics=[
                {
                    'Id': 'errors',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': self.namespace,
                            'MetricName': 'InvocationErrors',
                            'Dimensions': [
                                {'Name': 'ModelId', 'Value': self.model_id}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Sum'
                    },
                    'ReturnData': False
                },
                {
                    'Id': 'invocations',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': self.namespace,
                            'MetricName': 'Invocations',
                            'Dimensions': [
                                {'Name': 'ModelId', 'Value': self.model_id}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Sum'
                    },
                    'ReturnData': False
                },
                {
                    'Id': 'error_rate',
                    'Expression': '(errors / invocations) * 100',
                    'Label': 'Error Rate %',
                    'ReturnData': True
                }
            ],
            EvaluationPeriods=evaluation_periods,
            Threshold=threshold_percent,
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching',
            AlarmActions=[self.alarm_topic_arn] if self.alarm_topic_arn else []
        )

    def create_latency_alarm(
        self,
        alarm_name: str,
        threshold_ms: float = 5000,
        percentile: str = 'p99'
    ):
        """Create alarm for latency degradation"""

        self.cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription=f'Bedrock {percentile} latency exceeds {threshold_ms}ms',
            Namespace=self.namespace,
            MetricName='InvocationLatency',
            Dimensions=[
                {'Name': 'ModelId', 'Value': self.model_id}
            ],
            ExtendedStatistic=percentile,
            Period00,
            EvaluationPeriods=3,
            Threshold=threshold_ms,
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching',
            AlarmActions=[self.alarm_topic_arn] if self.alarm_topic_arn else []
        )

    def create_throttle_alarm(
        self,
        alarm_name: str,
        threshold: int = 10
    ):
        """Create alarm for throttling"""

        self.cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription=f'Bedrock throttles exceed {threshold} per minute',
            Namespace=self.namespace,
            MetricName='InvocationThrottles',
            Dimensions=[
                {'Name': 'ModelId', 'Value': self.model_id}
            ],
            Statistic='Sum',
            Period`,
            EvaluationPeriods=2,
            Threshold=threshold,
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching',
            AlarmActions=[self.alarm_topic_arn] if self.alarm_topic_arn else []
        )

    def create_cost_alarm(
        self,
        alarm_name: str,
        hourly_token_threshold: int = 1000000
    ):
        """Create alarm for token usage (cost proxy)"""

        self.cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription=f'Hourly token usage exceeds {hourly_token_threshold}',
            Metrics=[
                {
                    'Id': 'input_tokens',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': self.namespace,
                            'MetricName': 'InputTokenCount',
                            'Dimensions': [
                                {'Name': 'ModelId', 'Value': self.model_id}
                            ]
                        },
                        'Period': 3600,
                        'Stat': 'Sum'
                    },
                    'ReturnData': False
                },
                {
                    'Id': 'output_tokens',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': self.namespace,
                            'MetricName': 'OutputTokenCount',
                            'Dimensions': [
                                {'Name': 'ModelId', 'Value': self.model_id}
                            ]
                        },
                        'Period': 3600,
                        'Stat': 'Sum'
                    },
                    'ReturnData': False
                },
                {
                    'Id': 'total_tokens',
                    'Expression': 'input_tokens + output_tokens',
                    'Label': 'Total Tokens',
                    'ReturnData': True
                }
            ],
            EvaluationPeriods=1,
            Threshold=hourly_token_threshold,
            ComparisonOperator='GreaterThanThreshold',
            TreatMissingData='notBreaching',
            AlarmActions=[self.alarm_topic_arn] if self.alarm_topic_arn else []
        )

    def create_dashboard(self, dashboard_name: str):
        """Create comprehensive Bedrock monitoring dashboard"""

        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "x": 0, "y": 0, "width": 12, "height": 6,
                    "properties": {
                        "title": "Invocation Latency",
                        "metrics": [
                            [self.namespace, "InvocationLatency", "ModelId", self.model_id,
                             {"stat": "p50", "label": "p50"}],
                            ["...", {"stat": "p90", "label": "p90"}],
                            ["...", {"stat": "p99", "label": "p99"}]
                        ],
                        "period": 60,
                        "region": "us-east-1"
                    }
                },
                {
                    "type": "metric",
                    "x": 12, "y": 0, "width": 12, "height": 6,
                    "properties": {
                        "title": "Token Usage",
                        "metrics": [
                            [self.namespace, "InputTokenCount", "ModelId", self.model_id,
                             {"stat": "Sum", "label": "Input Tokens"}],
                            [self.namespace, "OutputTokenCount", "ModelId", self.model_id,
                             {"stat": "Sum", "label": "Output Tokens"}]
                        ],
                        "period": 300,
                        "stacked": True
                    }
                },
                {
                    "type": "metric",
                    "x": 0, "y": 6, "width": 8, "height": 6,
                    "properties": {
                        "title": "Invocations & Errors",
                        "metrics": [
                            [self.namespace, "Invocations", "ModelId", self.model_id,
                             {"stat": "Sum", "label": "Invocations"}],
                            [self.namespace, "InvocationErrors", "ModelId", self.model_id,
                             {"stat": "Sum", "label": "Errors", "color": "#d62728"}]
                        ],
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 8, "y": 6, "width": 8, "height": 6,
                    "properties": {
                        "title": "Throttling",
                        "metrics": [
                            [self.namespace, "InvocationThrottles", "ModelId", self.model_id,
                             {"stat": "Sum", "label": "Throttles", "color": "#ff7f0e"}]
                        ],
                        "period": 60
                    }
                },
                {
                    "type": "metric",
                    "x": 16, "y": 6, "width": 8, "height": 6,
                    "properties": {
                        "title": "Error Rate",
                        "metrics": [
                            [{
                                "expression": "(m1 / m2) * 100",
                                "label": "Error Rate %",
                                "id": "e1"
                            }],
                            [self.namespace, "InvocationErrors", "ModelId", self.model_id,
                             {"id": "m1", "visible": False}],
                            [self.namespace, "Invocations", "ModelId", self.model_id,
                             {"id": "m2", "visible": False}]
                        ],
                        "period": 300
                    }
                }
            ]
        }

        self.cloudwatch.put_dashboard(
            DashboardNameshboard_name,
            DashboardBody=str(dashboard_body).replace("'", '"')
        )


# Example: Set up monitoring
monitoring = BedrockMonitoringSetup(
    model_id='anthropic.claude-3-haiku-20240307-v1:0',
    alarm_topic_arn='arn:aws:sns:us-east-1:123456789012:bedrock-alerts'
)

# Create alarms
monitoring.create_error_rate_alarm(
    alarm_name='bedrock-high-error-rate',
    threshold_percent=5.0
)

monitoring.create_latency_alarm(
    alarm_name='bedrock-high-latency',
    threshold_msP00,
    percentile='p99'
)

monitoring.create_throttle_alarm(
    alarm_name='bedrock-throttling',
    threshold
)

monitoring.create_cost_alarm(
    alarm_name='bedrock-high-usage',
    hourly_token_thresholdP0000
)

# Create dashboard
monitoring.create_dashboard('Bedrock-Monitoring')

# Get metrics report
end_time = datetime.utcnow()
start_time = end_time - timedelta(hours$)

metrics = monitoring.get_metrics(
    metric_names=['Invocations', 'InvocationLatency', 'InputTokenCount', 'OutputTokenCount'],
    start_time=start_time,
    end_time=end_time,
    period600
)

print("24-Hour Metrics Summary:")
for metric_name, datapoints in metrics.items():
    if datapoints:
        total = sum(dp.get('Sum', dp.get('Average', 0)) for dp in datapoints)
        print(f"  {metric_name}: {total:,.0f}")