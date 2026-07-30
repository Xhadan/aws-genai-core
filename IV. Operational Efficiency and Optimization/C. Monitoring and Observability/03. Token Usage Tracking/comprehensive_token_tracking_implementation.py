import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
import json

class TokenUsageTracker:
    """Track and analyze token usage for cost management"""

    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.bedrock = boto3.client('bedrock-runtime')
        self.ce = boto3.client('ce')

        # Model pricing (update with current rates)
        self.pricing = {
            'anthropic.claude-3-haiku-20240307-v1:0': {
                'input': 0.00025,
                'output': 0.00125
            },
            'anthropic.claude-3-5-sonnet-20241022-v2:0': {
                'input': 0.003,
                'output': 0.015
            },
            'anthropic.claude-3-opus-20240229-v1:0': {
                'input': 0.015,
                'output': 0.075
            }
        }

    def invoke_with_tracking(
        self,
        model_id: str,
        prompt: str,
        metadata: Dict[str, str] = None,
        max_tokens: int = 500
    ) -> Dict:
        """Invoke model and track all token usage"""
        start_time = datetime.utcnow()

        response = self.bedrock.converse(
            modelId=model_id,
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': max_tokens}
        )

        usage = response.get('usage', {})
        input_tokens = usage.get('inputTokens', 0)
        output_tokens = usage.get('outputTokens', 0)

        # Calculate cost
        cost = self._calculate_cost(model_id, input_tokens, output_tokens)

        # Publish custom metrics for attribution
        self._publish_usage_metrics(
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            metadata=metadata or {}
        )

        return {
            'response': response['output']['message']['content'][0]['text'],
            'usage': {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'cost': cost
            },
            'metadata': metadata
        }

    def _calculate_cost(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for token usage"""
        rates = self.pricing.get(model_id, {'input': 0.003, 'output': 0.015})
        input_cost = (input_tokens / 1000) * rates['input']
        output_cost = (output_tokens / 1000) * rates['output']
        return input_cost + output_cost

    def _publish_usage_metrics(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        metadata: Dict[str, str]
    ):
        """Publish custom metrics for cost attribution"""
        timestamp = datetime.utcnow()

        # Build dimensions from metadata
        dimensions = [{'Name': 'ModelId', 'Value': model_id}]
        for key, value in metadata.items():
            dimensions.append({'Name': key, 'Value': value})

        metrics = [
            {
                'MetricName': 'InputTokens',
                'Dimensions': dimensions,
                'Timestamp': timestamp,
                'Value': input_tokens,
                'Unit': 'Count'
            },
            {
                'MetricName': 'OutputTokens',
                'Dimensions': dimensions,
                'Timestamp': timestamp,
                'Value': output_tokens,
                'Unit': 'Count'
            },
            {
                'MetricName': 'TotalTokens',
                'Dimensions': dimensions,
                'Timestamp': timestamp,
                'Value': input_tokens + output_tokens,
                'Unit': 'Count'
            },
            {
                'MetricName': 'EstimatedCost',
                'Dimensions': dimensions,
                'Timestamp': timestamp,
                'Value': cost,
                'Unit': 'None'
            }
        ]

        self.cloudwatch.put_metric_data(
            Namespace='GenAI/TokenUsage',
            MetricData=metrics
        )

    def get_usage_by_dimension(
        self,
        dimension_name: str,
        dimension_value: str,
        days: int = 7
    ) -> Dict:
        """Get token usage for specific dimension value"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(daysys)

        metrics = {}
        for metric_name in ['InputTokens', 'OutputTokens', 'EstimatedCost']:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='GenAI/TokenUsage',
                MetricName=metric_name,
                Dimensions=[
                    {'Name': dimension_name, 'Value': dimension_value}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Periodys * 24 * 3600,
                Statistics=['Sum']
            )

            datapoints = response.get('Datapoints', [])
            metrics[metric_name] = datapoints[0]['Sum'] if datapoints else 0

        return {
            'dimension': {dimension_name: dimension_value},
            'period_days': days,
            'input_tokens': metrics.get('InputTokens', 0),
            'output_tokens': metrics.get('OutputTokens', 0),
            'total_tokens': metrics.get('InputTokens', 0) + metrics.get('OutputTokens', 0),
            'estimated_cost': metrics.get('EstimatedCost', 0)
        }

    def get_cost_explorer_data(
        self,
        days: int = 30,
        granularity: str = 'DAILY'
    ) -> Dict:
        """Get actual Bedrock costs from Cost Explorer"""
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
        start_date = (datetime.utcnow() - timedelta(daysys)).strftime('%Y-%m-%d')

        response = self.ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity=granularity,
            Metrics=['UnblendedCost', 'UsageQuantity'],
            Filter={
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': ['Amazon Bedrock']
                }
            },
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
            ]
        )

        # Process results
        daily_costs = []
        for result in response.get('ResultsByTime', []):
            period_start = result['TimePeriod']['Start']
            groups = result.get('Groups', [])

            daily_total = 0
            breakdown = {}
            for group in groups:
                usage_type = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                daily_total += cost
                breakdown[usage_type] = cost

            daily_costs.append({
                'date': period_start,
                'total_cost': daily_total,
                'breakdown': breakdown
            })

        return {
            'period_days': days,
            'daily_costs': daily_costs,
            'total_cost': sum(d['total_cost'] for d in daily_costs)
        }


class CostAllocationReporter:
    """Generate cost allocation reports"""

    def __init__(self, tracker: TokenUsageTracker):
        self.tracker = tracker
        self.cloudwatch = boto3.client('cloudwatch')

    def generate_team_report(
        self,
        teams: List[str],
        days: int = 30
    ) -> Dict:
        """Generate cost report by team"""
        report = {
            'period_days': days,
            'generated_at': datetime.utcnow().isoformat(),
            'teams': {}
        }

        total_cost = 0
        for team in teams:
            usage = self.tracker.get_usage_by_dimension(
                dimension_name='Team',
                dimension_value=team,
                daysys
            )
            report['teams'][team] = {
                'input_tokens': usage['input_tokens'],
                'output_tokens': usage['output_tokens'],
                'total_tokens': usage['total_tokens'],
                'estimated_cost': usage['estimated_cost']
            }
            total_cost += usage['estimated_cost']

        report['total_cost'] = total_cost

        # Calculate percentages
        for team in teams:
            if total_cost > 0:
                report['teams'][team]['percentage'] = (
                    report['teams'][team]['estimated_cost'] / total_cost * 100
                )
            else:
                report['teams'][team]['percentage'] = 0

        return report

    def generate_model_report(
        self,
        model_ids: List[str],
        days: int = 30
    ) -> Dict:
        """Generate cost report by model"""
        report = {
            'period_days': days,
            'generated_at': datetime.utcnow().isoformat(),
            'models': {}
        }

        for model_id in model_ids:
            usage = self.tracker.get_usage_by_dimension(
                dimension_name='ModelId',
                dimension_value=model_id,
                daysys
            )
            report['models'][model_id] = usage

        report['total_cost'] = sum(
            m['estimated_cost'] for m in report['models'].values()
        )

        return report


# Example usage
tracker = TokenUsageTracker()

# Track usage with team attribution
result = tracker.invoke_with_tracking(
    model_id='anthropic.claude-3-haiku-20240307-v1:0',
    prompt='Explain cloud computing in one sentence.',
    metadata={
        'Team': 'Engineering',
        'Project': 'Documentation',
        'Environment': 'Production'
    }
)

print(f"Response: {result['response']}")
print(f"Tokens: {result['usage']['total_tokens']}")
print(f"Cost: ${result['usage']['cost']:.6f}")

# Generate team report
reporter = CostAllocationReporter(tracker)
team_report = reporter.generate_team_report(
    teams=['Engineering', 'Marketing', 'Support'],
    days0
)

print("\n30-Day Team Cost Report:")
for team, data in team_report['teams'].items():
    print(f"  {team}: ${data['estimated_cost']:.2f} ({data['percentage']:.1f}%)")