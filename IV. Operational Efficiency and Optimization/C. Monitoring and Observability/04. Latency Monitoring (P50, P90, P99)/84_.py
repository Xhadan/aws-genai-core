import boto3
from datetime import datetime, timedelta
import math

class LatencyAnomalyDetector:
    """Detect latency anomalies using CloudWatch Anomaly Detection"""

    def __init__(self, region: str = 'us-east-1'):
        self.cloudwatch = boto3.client(
            'cloudwatch',
            region_name=region
        )
        self.namespace = 'GenAI/Latency'

    def create_anomaly_detector(
        self,
        model_id: str,
        metric_name: str = 'TTLT'
    ):
        """
        Create CloudWatch anomaly detector for latency metric.

        The detector learns normal patterns over 2 weeks and
        automatically adjusts for daily/weekly seasonality.
        """
        self.cloudwatch.put_anomaly_detector(
            Namespace=self.namespace,
            MetricName=metric_name,
            Dimensions=[
                {'Name': 'ModelId', 'Value': model_id}
            ],
            Stat='Average',
            Configuration={
                'ExcludedTimeRanges': [],  # Can exclude maintenance windows
                'MetricTimezone': 'UTC'
            }
        )

        print(f"Created anomaly detector for {metric_name} on {model_id}")

    def create_anomaly_alarm(
        self,
        model_id: str,
        metric_name: str,
        sns_topic_arn: str,
        anomaly_band_width: float = 2.0
    ):
        """
        Create alarm that triggers on anomalous latency.

        Args:
            model_id: Model to monitor
            metric_name: Metric to monitor
            sns_topic_arn: SNS topic for alerts
            anomaly_band_width: Standard deviations for anomaly band
        """
        alarm_name = f"Latency-Anomaly-{metric_name}-{model_id.split('.')[-1]}"

        self.cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription=f'Anomalous {metric_name} detected for {model_id}',
            Metrics=[
                {
                    'Id': 'm1',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': self.namespace,
                            'MetricName': metric_name,
                            'Dimensions': [
                                {'Name': 'ModelId', 'Value': model_id}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Average'
                    },
                    'ReturnData': True
                },
                {
                    'Id': 'ad1',
                    'Expression': f'ANOMALY_DETECTION_BAND(m1, {anomaly_band_width})',
                    'Label': 'AnomalyBand',
                    'ReturnData': True
                }
            ],
            ThresholdMetricId='ad1',
            ComparisonOperator='LessThanLowerOrGreaterThanUpperThreshold',
            EvaluationPeriods=3,
            TreatMissingData='notBreaching',
            ActionsEnabled=True,
            AlarmActions=[sns_topic_arn]
        )

        print(f"Created anomaly alarm: {alarm_name}")

    def analyze_recent_anomalies(
        self,
        model_id: str,
        metric_name: str = 'TTLT',
        hours: int = 24
    ) -> List[Dict]:
        """
        Identify anomalous periods in recent data.

        Uses statistical analysis when anomaly detector
        data is not yet available.
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # Get metric data
        response = self.cloudwatch.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'latency',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': self.namespace,
                            'MetricName': metric_name,
                            'Dimensions': [
                                {'Name': 'ModelId', 'Value': model_id}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Average'
                    },
                    'ReturnData': True
                }
            ],
            StartTime=start_time,
            EndTime=end_time
        )

        values = response['MetricDataResults'][0]['Values']
        timestamps = response['MetricDataResults'][0]['Timestamps']

        if len(values) < 10:
            return []

        # Calculate statistics
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)

        # Identify anomalies (beyond 2 standard deviations)
        anomalies = []
        threshold_high = mean + (2 * std_dev)
        threshold_low = mean - (2 * std_dev)

        for timestamp, value in zip(timestamps, values):
            if value > threshold_high or value < threshold_low:
                anomalies.append({
                    'timestamp': timestamp.isoformat(),
                    'value_ms': value,
                    'expected_range': {
                        'low': max(0, threshold_low),
                        'high': threshold_high
                    },
                    'deviation_factor': abs(value - mean) / std_dev
                })

        return anomalies


# Example usage
detector = LatencyAnomalyDetector()

# Create anomaly detector for TTFB and TTLT
model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
detector.create_anomaly_detector(model_id, 'TTFB')
detector.create_anomaly_detector(model_id, 'TTLT')

# Analyze recent anomalies
anomalies = detector.analyze_recent_anomalies(model_id, hours=24)
for anomaly in anomalies:
    print(f"Anomaly at {anomaly['timestamp']}: {anomaly['value_ms']:.0f}ms "
          f"(expected {anomaly['expected_range']['low']:.0f}-{anomaly['expected_range']['high']:.0f}ms)")