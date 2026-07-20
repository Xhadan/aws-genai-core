import boto3
import json
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')
logs = boto3.client('logs')

class GenAIMonitor:
    """
    Monitor GenAI application quality and safety.
    """

    def __init__(self, application_name, log_group):
        self.application_name = application_name
        self.log_group = log_group

    def log_interaction(self, interaction_data):
        """
        Log interaction details for analysis.
        """
        log_entry = {
            'timestamp': str(datetime.utcnow()),
            'application': self.application_name,
            'request_id': interaction_data.get('request_id'),
            'model_id': interaction_data.get('model_id'),
            'latency_ms': interaction_data.get('latency_ms'),
            'input_tokens': interaction_data.get('input_tokens'),
            'output_tokens': interaction_data.get('output_tokens'),
            'guardrail_action': interaction_data.get('guardrail_action', 'none'),
            'guardrail_filters_triggered': interaction_data.get('filters_triggered', []),
            'relevance_score': interaction_data.get('relevance_score'),
            'grounding_score': interaction_data.get('grounding_score'),
            'user_feedback': interaction_data.get('user_feedback')
        }

        # Calculate estimated cost (example pricing)
        input_cost = (interaction_data.get('input_tokens', 0) / 1000) * 0.003
        output_cost = (interaction_data.get('output_tokens', 0) / 1000) * 0.015
        log_entry['estimated_cost'] = input_cost + output_cost

        # Put log event
        logs.put_log_events(
            logGroupName=self.log_group,
            logStreamName=f"interactions-{datetime.utcnow().strftime('%Y-%m-%d')}",
            logEvents=[{
                'timestamp': int(datetime.utcnow().timestamp() * 1000),
                'message': json.dumps(log_entry)
            }]
        )

        # Publish metrics
        self._publish_metrics(log_entry)

        return log_entry

    def _publish_metrics(self, log_entry):
        """
        Publish custom metrics from interaction.
        """
        metrics = [
            {
                'MetricName': 'InteractionLatency',
                'Value': log_entry.get('latency_ms', 0),
                'Unit': 'Milliseconds'
            },
            {
                'MetricName': 'InputTokens',
                'Value': log_entry.get('input_tokens', 0),
                'Unit': 'Count'
            },
            {
                'MetricName': 'OutputTokens',
                'Value': log_entry.get('output_tokens', 0),
                'Unit': 'Count'
            },
            {
                'MetricName': 'EstimatedCost',
                'Value': log_entry.get('estimated_cost', 0),
                'Unit': 'None'
            }
        ]

        # Guardrail metrics
        if log_entry.get('guardrail_action') != 'none':
            metrics.append({
                'MetricName': 'GuardrailTriggered',
                'Value': 1,
                'Unit': 'Count'
            })

            if log_entry.get('guardrail_action') = 'BLOCKED':
                metrics.append({
                    'MetricName': 'ContentBlocked',
                    'Value': 1,
                    'Unit': 'Count'
                })

        # Quality metrics
        if log_entry.get('relevance_score'):
            metrics.append({
                'MetricName': 'RelevanceScore',
                'Value': log_entry['relevance_score'],
                'Unit': 'None'
            })

        if log_entry.get('user_feedback'):
            feedback_value = 1 if log_entry['user_feedback'] = 'positive' else 0
            metrics.append({
                'MetricName': 'PositiveFeedbackRate',
                'Value': feedback_value,
                'Unit': 'None'
            })

        # Publish to CloudWatch
        metric_data = []
        for m in metrics:
            metric_data.append({
                'MetricName': m['MetricName'],
                'Value': m['Value'],
                'Unit': m['Unit'],
                'Timestamp': datetime.utcnow(),
                'Dimensions': [
                    {'Name': 'Application', 'Value': self.application_name}
                ]
            })

        cloudwatch.put_metric_data(
            Namespace='Custom/GenAI',
            MetricData=metric_data
        )

    def analyze_safety_trends(self, hours$):
        """
        Analyze safety-related trends from logs.
        """
        query = """
        fields @timestamp, guardrail_action, guardrail_filters_triggered
        | filter guardrail_action != 'none'
        | stats count(*) as trigger_count by guardrail_action, guardrail_filters_triggered
        | sort trigger_count desc
        """

        response = logs.start_query(
            logGroupName=self.log_group,
            startTime=int((datetime.utcnow() - timedelta(hours=hours)).timestamp()),
            endTime=int(datetime.utcnow().timestamp()),
            queryString=query
        )

        # Wait for query to complete
        import time
        query_id = response['queryId']
        while True:
            result = logs.get_query_results(queryId=query_id)
            if result['status'] = 'Complete':
                break
            time.sleep(1)

        return result['results']

    def get_quality_metrics_summary(self, hours$):
        """
        Get summary of quality metrics.
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        metrics_to_fetch = [
            ('RelevanceScore', 'Average'),
            ('PositiveFeedbackRate', 'Average'),
            ('GuardrailTriggered', 'Sum'),
            ('ContentBlocked', 'Sum'),
            ('InteractionLatency', 'p99')
        ]

        summary = {}
        for metric_name, stat in metrics_to_fetch:
            response = cloudwatch.get_metric_statistics(
                Namespace='Custom/GenAI',
                MetricName=metric_name,
                Dimensions=[{'Name': 'Application', 'Value': self.application_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period600 * hours,  # Single period for summary
                Statistics=[stat] if stat != 'p99' else [],
                ExtendedStatistics=['p99'] if stat = 'p99' else []
            )

            if response['Datapoints']:
                if stat = 'p99':
                    summary[metric_name] = response['Datapoints'][0].get('ExtendedStatistics', {}).get('p99')
                else:
                    summary[metric_name] = response['Datapoints'][0].get(stat)

        return summary


# Example usage
monitor = GenAIMonitor(
    application_name='CustomerSupportBot',
    log_group='/genai/customer-support/interactions'
)

# Log an interaction
monitor.log_interaction({
    'request_id': 'req-123',
    'model_id': 'anthropic.claude-3-sonnet',
    'latency_ms': 1250,
    'input_tokens': 150,
    'output_tokens': 320,
    'guardrail_action': 'INTERVENED',
    'filters_triggered': ['PII_FILTER'],
    'relevance_score': 0.85,
    'user_feedback': 'positive'
})

# Get summary
summary = monitor.get_quality_metrics_summary(hours$)
print("== 24-Hour Quality Summary ==")
for metric, value in summary.items():
    print(f"  {metric}: {value}")