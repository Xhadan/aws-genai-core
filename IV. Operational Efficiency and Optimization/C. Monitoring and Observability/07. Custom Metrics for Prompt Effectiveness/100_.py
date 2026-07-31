import boto3
import json

class MetricsDashboardBuilder:
    """Build CloudWatch dashboards for GenAI custom metrics"""

    def __init__(self, region: str = 'us-east-1'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.region = region

    def create_quality_dashboard(
        self,
        dashboard_name: str = 'GenAI-Quality-Dashboard'
    ):
        """Create dashboard for quality and business metrics"""
        dashboard_body = {
            'widgets': [
                # Quality Score Trends
                {
                    'type': 'metric',
                    'x': 0, 'y': 0,
                    'width': 12, 'height': 6,
                    'properties': {
                        'title': 'Quality Scores by Dimension',
                        'metrics': [
                            ['GenAI/Quality', 'QualityScore', 'Dimension', 'relevance'],
                            ['...', 'helpfulness'],
                            ['...', 'accuracy'],
                            ['...', 'coherence']
                        ],
                        'period': 300,
                        'stat': 'Average',
                        'region': self.region
                    }
                },
                # Overall Quality Score
                {
                    'type': 'metric',
                    'x': 12, 'y': 0,
                    'width': 6, 'height': 6,
                    'properties': {
                        'title': 'Overall Quality Score',
                        'metrics': [
                            ['GenAI/Quality', 'OverallQualityScore']
                        ],
                        'period': 300,
                        'stat': 'Average',
                        'view': 'gauge',
                        'yAxis': {'left': {'min': 0, 'max': 1}},
                        'region': self.region
                    }
                },
                # User Satisfaction
                {
                    'type': 'metric',
                    'x': 18, 'y': 0,
                    'width': 6, 'height': 6,
                    'properties': {
                        'title': 'User Satisfaction Rate',
                        'metrics': [
                            ['GenAI/Business', 'SatisfactionRate']
                        ],
                        'period': 3600,
                        'stat': 'Average',
                        'view': 'gauge',
                        'yAxis': {'left': {'min': 0, 'max': 1}},
                        'region': self.region
                    }
                },
                # Task Completion Rate
                {
                    'type': 'metric',
                    'x': 0, 'y': 6,
                    'width': 8, 'height': 6,
                    'properties': {
                        'title': 'Task Completion by Type',
                        'metrics': [
                            [{'expression': 'm2/m1*100', 'label': 'Completion Rate %', 'id': 'e1'}],
                            ['GenAI/Business', 'TasksAttempted', 'TaskType', 'inquiry_resolution', {'id': 'm1', 'visible': False}],
                            ['...', 'TasksCompleted', '.', '.', {'id': 'm2', 'visible': False}]
                        ],
                        'period': 3600,
                        'stat': 'Sum',
                        'region': self.region
                    }
                },
                # Feedback Distribution
                {
                    'type': 'metric',
                    'x': 8, 'y': 6,
                    'width': 8, 'height': 6,
                    'properties': {
                        'title': 'Feedback Distribution',
                        'metrics': [
                            ['GenAI/Business', 'PositiveFeedback'],
                            ['GenAI/Business', 'NegativeFeedback']
                        ],
                        'period': 3600,
                        'stat': 'Sum',
                        'view': 'pie',
                        'region': self.region
                    }
                },
                # Regeneration Rate (Quality Signal)
                {
                    'type': 'metric',
                    'x': 16, 'y': 6,
                    'width': 8, 'height': 6,
                    'properties': {
                        'title': 'Response Regeneration Rate',
                        'metrics': [
                            ['GenAI/Business', 'Regenerations'],
                            ['GenAI/Business', 'ConversationsStarted']
                        ],
                        'period': 3600,
                        'stat': 'Sum',
                        'region': self.region
                    }
                },
                # Conversation Metrics
                {
                    'type': 'metric',
                    'x': 0, 'y': 12,
                    'width': 12, 'height': 6,
                    'properties': {
                        'title': 'Conversation Metrics',
                        'metrics': [
                            ['GenAI/Business', 'MessagesPerConversation', {'stat': 'Average'}],
                            ['GenAI/Business', 'TokensPerConversation', {'stat': 'Average', 'yAxis': 'right'}]
                        ],
                        'period': 3600,
                        'region': self.region
                    }
                },
                # Conversations Started
                {
                    'type': 'metric',
                    'x': 12, 'y': 12,
                    'width': 12, 'height': 6,
                    'properties': {
                        'title': 'Conversations Over Time',
                        'metrics': [
                            ['GenAI/Business', 'ConversationsStarted', {'stat': 'Sum'}]
                        ],
                        'period': 3600,
                        'region': self.region
                    }
                }
            ]
        }

        self.cloudwatch.put_dashboard(
            DashboardNameshboard_name,
            DashboardBody=json.dumps(dashboard_body)
        )

        print(f"Created dashboard: {dashboard_name}")

    def create_quality_alarm(
        self,
        sns_topic_arn: str,
        threshold: float = 0.7
    ):
        """Create alarm for quality score degradation"""
        self.cloudwatch.put_metric_alarm(
            AlarmName='GenAI-QualityScore-Degradation',
            AlarmDescription='Overall quality score dropped below threshold',
            Namespace='GenAI/Quality',
            MetricName='OverallQualityScore',
            Statistic='Average',
            Period=300,
            EvaluationPeriods=3,
            Threshold=threshold,
            ComparisonOperator='LessThanThreshold',
            TreatMissingData='notBreaching',
            ActionsEnabled=True,
            AlarmActions=[sns_topic_arn]
        )

        print(f"Created quality alarm with threshold {threshold}")


# Example usage
builder = MetricsDashboardBuilder()
builder.create_quality_dashboard('GenAI-Quality-Dashboard')
builder.create_quality_alarm(
    sns_topic_arn='arn:aws:sns:us-east-1:123456789012:alerts',
    threshold=0.75
)