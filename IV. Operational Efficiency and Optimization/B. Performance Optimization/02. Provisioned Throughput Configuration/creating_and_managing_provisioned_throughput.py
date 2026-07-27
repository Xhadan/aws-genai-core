import boto3
from datetime import datetime, timedelta
from typing import Optional, Dict, List

bedrock = boto3.client('bedrock')
bedrock_runtime = boto3.client('bedrock-runtime')
cloudwatch = boto3.client('cloudwatch')

class ProvisionedThroughputManager:
    """Manage provisioned throughput for Amazon Bedrock"""

    def __init__(self):
        self.bedrock = boto3.client('bedrock')
        self.bedrock_runtime = boto3.client('bedrock-runtime')

    def create_provisioned_throughput(
        self,
        model_id: str,
        throughput_name: str,
        model_units: int,
        commitment: Optional[str] = None
    ) -> str:
        """
        Create provisioned throughput for a model.

        Args:
            model_id: Base model ID (e.g., 'anthropic.claude-3-sonnet-20240229-v1:0')
            throughput_name: Unique name for this provisioned throughput
            model_units: Number of model units to provision
            commitment: 'OneMonth', 'SixMonths', or None for no commitment

        Returns:
            Provisioned model ARN
        """
        params = {
            'modelId': model_id,
            'provisionedModelName': throughput_name,
            'modelUnits': model_units
        }

        if commitment:
            params['commitmentDuration'] = commitment

        response = self.bedrock.create_provisioned_model_throughput(**params)

        return response['provisionedModelArn']

    def get_throughput_status(self, provisioned_model_id: str) -> Dict:
        """Get status and details of provisioned throughput"""
        response = self.bedrock.get_provisioned_model_throughput(
            provisionedModelId=provisioned_model_id
        )

        return {
            'name': response['provisionedModelName'],
            'arn': response['provisionedModelArn'],
            'status': response['status'],
            'model_id': response['modelId'],
            'model_units': response['modelUnits'],
            'commitment': response.get('commitmentDuration', 'NoCommitment'),
            'commitment_expiration': response.get('commitmentExpirationTime'),
            'created_at': response.get('creationTime')
        }

    def update_model_units(
        self,
        provisioned_model_id: str,
        new_model_units: int
    ) -> Dict:
        """
        Update the number of model units.
        Can increase at any time, decrease only to commitment minimum.
        """
        response = self.bedrock.update_provisioned_model_throughput(
            provisionedModelId=provisioned_model_id,
            desiredModelUnits=new_model_units
        )

        return self.get_throughput_status(provisioned_model_id)

    def list_provisioned_throughputs(self) -> List[Dict]:
        """List all provisioned throughputs"""
        response = self.bedrock.list_provisioned_model_throughputs()

        throughputs = []
        for pt in response.get('provisionedModelSummaries', []):
            throughputs.append({
                'name': pt['provisionedModelName'],
                'arn': pt['provisionedModelArn'],
                'status': pt['status'],
                'model_id': pt['modelId'],
                'model_units': pt['modelUnits']
            })

        return throughputs

    def delete_provisioned_throughput(self, provisioned_model_id: str):
        """
        Delete provisioned throughput.
        Note: Cannot delete if commitment is active.
        """
        self.bedrock.delete_provisioned_model_throughput(
            provisionedModelId=provisioned_model_id
        )

    def invoke_with_provisioned(
        self,
        provisioned_model_arn: str,
        prompt: str,
        max_tokens: int = 500
    ) -> Dict:
        """Invoke model using provisioned throughput"""
        response = self.bedrock_runtime.converse(
            modelId=provisioned_model_arn,  # Use ARN, not model ID
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': max_tokens}
        )

        return {
            'response': response['output']['message']['content'][0]['text'],
            'usage': response.get('usage', {})
        }


class CapacityPlanner:
    """Plan provisioned throughput capacity based on usage patterns"""

    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')

    def analyze_current_usage(
        self,
        model_id: str,
        days: int = 7
    ) -> Dict:
        """Analyze token usage patterns from CloudWatch"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(daysys)

        # Get input token metrics
        input_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Bedrock',
            MetricName='InputTokenCount',
            Dimensions=[
                {'Name': 'ModelId', 'Value': model_id}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period`,  # 1 minute granularity
            Statistics=['Sum', 'Maximum']
        )

        # Get output token metrics
        output_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Bedrock',
            MetricName='OutputTokenCount',
            Dimensions=[
                {'Name': 'ModelId', 'Value': model_id}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period`,
            Statistics=['Sum', 'Maximum']
        )

        # Calculate statistics
        input_datapoints = input_response.get('Datapoints', [])
        output_datapoints = output_response.get('Datapoints', [])

        if not input_datapoints:
            return {'error': 'No data available'}

        total_input = sum(dp['Sum'] for dp in input_datapoints)
        total_output = sum(dp['Sum'] for dp in output_datapoints)
        peak_input = max(dp['Maximum'] for dp in input_datapoints) if input_datapoints else 0
        peak_output = max(dp['Maximum'] for dp in output_datapoints) if output_datapoints else 0

        return {
            'period_days': days,
            'total_input_tokens': total_input,
            'total_output_tokens': total_output,
            'peak_input_per_minute': peak_input,
            'peak_output_per_minute': peak_output,
            'peak_total_per_minute': peak_input + peak_output,
            'avg_input_per_minute': total_input / (days * 24 * 60),
            'avg_output_per_minute': total_output / (days * 24 * 60)
        }

    def recommend_model_units(
        self,
        usage_stats: Dict,
        model_id: str,
        buffer_percent: float = 30
    ) -> Dict:
        """Recommend MU count based on usage analysis"""

        # Model unit capacities (tokens/minute) - approximate
        mu_capacities = {
            'anthropic.claude-3-haiku-20240307-v1:0': 300000,
            'anthropic.claude-3-5-sonnet-20241022-v2:0': 100000,
            'anthropic.claude-3-opus-20240229-v1:0': 50000,
            'amazon.titan-text-express-v1': 200000
        }

        capacity_per_mu = mu_capacities.get(model_id, 100000)
        peak_tokens = usage_stats.get('peak_total_per_minute', 0)

        # Calculate with buffer
        required_capacity = peak_tokens * (1 + buffer_percent / 100)
        recommended_mus = max(1, int(required_capacity / capacity_per_mu) + 1)

        # Cost estimation (example rates)
        hourly_costs = {
            'no_commitment': 30,
            'one_month': 21,
            'six_months': 15
        }

        return {
            'peak_tokens_per_minute': peak_tokens,
            'buffer_percent': buffer_percent,
            'required_capacity': required_capacity,
            'capacity_per_mu': capacity_per_mu,
            'recommended_mus': recommended_mus,
            'estimated_monthly_cost': {
                'no_commitment': recommended_mus * hourly_costs['no_commitment'] * 24 * 30,
                'one_month': recommended_mus * hourly_costs['one_month'] * 24 * 30,
                'six_months': recommended_mus * hourly_costs['six_months'] * 24 * 30
            }
        }


# Example usage
manager = ProvisionedThroughputManager()
planner = CapacityPlanner()

# Analyze current usage
usage = planner.analyze_current_usage(
    model_id='anthropic.claude-3-5-sonnet-20241022-v2:0',
    days=7
)
print(f"Peak tokens/min: {usage.get('peak_total_per_minute', 'N/A')}")

# Get recommendation
recommendation = planner.recommend_model_units(
    usage_stats=usage,
    model_id='anthropic.claude-3-5-sonnet-20241022-v2:0',
    buffer_percent0
)
print(f"Recommended MUs: {recommendation['recommended_mus']}")
print(f"Monthly cost (6-mo commit): ${recommendation['estimated_monthly_cost']['six_months']:,.0f}")

# Create provisioned throughput
if recommendation['recommended_mus'] > 0:
    arn = manager.create_provisioned_throughput(
        model_id='anthropic.claude-3-5-sonnet-20241022-v2:0',
        throughput_name='production-sonnet-pt',
        model_units=recommendation['recommended_mus'],
        commitment='SixMonths'
    )
    print(f"Created: {arn}")