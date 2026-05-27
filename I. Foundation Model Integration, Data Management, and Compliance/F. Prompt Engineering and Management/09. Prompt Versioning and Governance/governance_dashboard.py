import boto3
from datetime import datetime, timedelta
from typing import Dict, List

cloudwatch = boto3.client('cloudwatch')

class PromptGovernanceDashboard:
    """Monitor prompt governance metrics."""

    def __init__(self, namespace: str = "PromptGovernance"):
        self.namespace = namespace
        self.cloudwatch = boto3.client('cloudwatch')

    def record_deployment(self, prompt_id: str, version: str,
                          environment: str, success: bool):
        """Record deployment metric."""
        self.cloudwatch.put_metric_data(
            Namespace=self.namespace,
            MetricData=[
                {
                    'MetricName': 'Deployments',
                    'Dimensions': [
                        {'Name': 'PromptId', 'Value': prompt_id},
                        {'Name': 'Environment', 'Value': environment},
                        {'Name': 'Status', 'Value': 'success' if success else 'failure'}
                    ],
                    'Value': 1,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )

    def record_approval_time(self, prompt_id: str, hours: float):
        """Record time from submission to approval."""
        self.cloudwatch.put_metric_data(
            Namespace=self.namespace,
            MetricData=[
                {
                    'MetricName': 'ApprovalTimeHours',
                    'Dimensions': [
                        {'Name': 'PromptId', 'Value': prompt_id}
                    ],
                    'Value': hours,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )

    def record_rollback(self, prompt_id: str, reason: str):
        """Record rollback event."""
        self.cloudwatch.put_metric_data(
            Namespace=self.namespace,
            MetricData=[
                {
                    'MetricName': 'Rollbacks',
                    'Dimensions': [
                        {'Name': 'PromptId', 'Value': prompt_id},
                        {'Name': 'Reason', 'Value': reason}
                    ],
                    'Value': 1,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )

    def record_quality_score(self, prompt_id: str, version: str, score: float):
        """Record quality score for a prompt version."""
        self.cloudwatch.put_metric_data(
            Namespace=self.namespace,
            MetricData=[
                {
                    'MetricName': 'QualityScore',
                    'Dimensions': [
                        {'Name': 'PromptId', 'Value': prompt_id},
                        {'Name': 'Version', 'Value': version}
                    ],
                    'Value': score,
                    'Unit': 'None',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )

    def create_alarm(self, prompt_id: str, metric: str, threshold: float):
        """Create CloudWatch alarm for prompt metrics."""
        self.cloudwatch.put_metric_alarm(
            AlarmName=f"PromptQuality-{prompt_id}",
            MetricName=metric,
            Namespace=self.namespace,
            Dimensions=[{'Name': 'PromptId', 'Value': prompt_id}],
            Statistic='Average',
            Period00,  # 5 minutes
            EvaluationPeriods=3,
            Threshold=threshold,
            ComparisonOperator='LessThanThreshold',
            AlarmActions=['arn:aws:sns:region:account:prompt-alerts'],
            AlarmDescription=f"Quality score below threshold for {prompt_id}"
        )

    def get_governance_summary(self) -> Dict:
        """Get summary of governance metrics."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)

        # Get deployment stats
        deployments = self.cloudwatch.get_metric_statistics(
            Namespace=self.namespace,
            MetricName='Deployments',
            StartTime=start_time,
            EndTime=end_time,
            Period400,  # Daily
            Statistics=['Sum']
        )

        # Get rollback stats
        rollbacks = self.cloudwatch.get_metric_statistics(
            Namespace=self.namespace,
            MetricName='Rollbacks',
            StartTime=start_time,
            EndTime=end_time,
            Period400,
            Statistics=['Sum']
        )

        return {
            'period': '7 days',
            'total_deployments': sum(d['Sum'] for d in deployments['Datapoints']),
            'total_rollbacks': sum(r['Sum'] for r in rollbacks['Datapoints']),
            'rollback_rate': (
                sum(r['Sum'] for r in rollbacks['Datapoints']) /
                max(sum(d['Sum'] for d in deployments['Datapoints']), 1)
            ) * 100
        }


# Example usage
dashboard = PromptGovernanceDashboard()

# Record events
dashboard.record_deployment("customer-support", "2.1.0", "production", True)
dashboard.record_quality_score("customer-support", "2.1.0", 0.92)

# Create alarm
dashboard.create_alarm("customer-support", "QualityScore", 0.8)

# Get summary
summary = dashboard.get_governance_summary()
print(f"Governance Summary: {summary}")