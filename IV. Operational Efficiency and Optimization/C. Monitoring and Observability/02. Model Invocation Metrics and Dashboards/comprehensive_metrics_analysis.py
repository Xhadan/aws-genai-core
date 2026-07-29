import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import statistics

class InvocationMetricsAnalyzer:
    """Analyze Bedrock model invocation metrics"""

    def __init__(self, model_id: str):
        self.cloudwatch = boto3.client('cloudwatch')
        self.model_id = model_id
        self.namespace = 'AWS/Bedrock'

    def get_invocation_summary(
        self,
        hours: int = 24
    ) -> Dict:
        """Get comprehensive invocation summary"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        metrics_config = {
            'Invocations': {'stat': 'Sum'},
            'InputTokenCount': {'stat': 'Sum'},
            'OutputTokenCount': {'stat': 'Sum'},
            'InvocationLatency': {'stat': 'Average'},
            'InvocationErrors': {'stat': 'Sum'},
            'InvocationThrottles': {'stat': 'Sum'}
        }

        results = {}
        for metric_name, config in metrics_config.items():
            response = self.cloudwatch.get_metric_statistics(
                Namespace=self.namespace,
                MetricName=metric_name,
                Dimensions=[{'Name': 'ModelId', 'Value': self.model_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=hours * 3600,
                Statistics=[config['stat']]
            )

            datapoints = response.get('Datapoints', [])
            if datapoints:
                results[metric_name] = datapoints[0].get(config['stat'], 0)
            else:
                results[metric_name] = 0

        # Calculate derived metrics
        invocations = results.get('Invocations', 0)
        if invocations > 0:
            results['ErrorRate'] = (results.get('InvocationErrors', 0) / invocations) * 100
            results['ThrottleRate'] = (results.get('InvocationThrottles', 0) / invocations) * 100
            results['AvgInputTokens'] = results.get('InputTokenCount', 0) / invocations
            results['AvgOutputTokens'] = results.get('OutputTokenCount', 0) / invocations
        else:
            results['ErrorRate'] = 0
            results['ThrottleRate'] = 0
            results['AvgInputTokens'] = 0
            results['AvgOutputTokens'] = 0

        return results

    def get_latency_percentiles(
        self,
        hours: int = 24
    ) -> Dict[str, float]:
        """Get latency percentile distribution"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        percentiles = ['p50', 'p90', 'p95', 'p99']
        results = {}

        for percentile in percentiles:
            response = self.cloudwatch.get_metric_statistics(
                Namespace=self.namespace,
                MetricName='InvocationLatency',
                Dimensions=[{'Name': 'ModelId', 'Value': self.model_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=hours * 3600,
                ExtendedStatistics=[percentile]
            )

            datapoints = response.get('Datapoints', [])
            if datapoints and percentile in datapoints[0].get('ExtendedStatistics', {}):
                results[percentile] = datapoints[0]['ExtendedStatistics'][percentile]
            else:
                results[percentile] = 0

        return results

    def get_hourly_trends(
        self,
        hours: int = 24
    ) -> Dict[str, List]:
        """Get hourly metric trends"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        metrics = ['Invocations', 'InputTokenCount', 'OutputTokenCount', 'InvocationLatency']
        trends = {}

        for metric in metrics:
            stat = 'Average' if metric = 'InvocationLatency' else 'Sum'

            response = self.cloudwatch.get_metric_statistics(
                Namespace=self.namespace,
                MetricName=metric,
                Dimensions=[{'Name': 'ModelId', 'Value': self.model_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period600,
                Statistics=[stat]
            )

            # Sort by timestamp
            datapoints = sorted(
                response.get('Datapoints', []),
                key=lambda x: x['Timestamp']
            )

            trends[metric] = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'value': dp.get(stat, 0)
                }
                for dp in datapoints
            ]

        return trends

    def estimate_costs(
        self,
        hours: int = 24,
        input_rate_per_1k: float = 0.00025,
        output_rate_per_1k: float = 0.00125
    ) -> Dict:
        """Estimate costs from token metrics"""
        summary = self.get_invocation_summary(hours)

        input_cost = (summary.get('InputTokenCount', 0) / 1000) * input_rate_per_1k
        output_cost = (summary.get('OutputTokenCount', 0) / 1000) * output_rate_per_1k
        total_cost = input_cost + output_cost

        invocations = summary.get('Invocations', 0)
        cost_per_invocation = total_cost / invocations if invocations > 0 else 0

        return {
            'period_hours': hours,
            'input_tokens': summary.get('InputTokenCount', 0),
            'output_tokens': summary.get('OutputTokenCount', 0),
            'total_tokens': summary.get('InputTokenCount', 0) + summary.get('OutputTokenCount', 0),
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': total_cost,
            'invocations': invocations,
            'cost_per_invocation': cost_per_invocation,
            'projected_daily_cost': (total_cost / hours) * 24,
            'projected_monthly_cost': (total_cost / hours) * 24 * 30
        }

    def get_error_analysis(
        self,
        hours: int = 24
    ) -> Dict:
        """Analyze error patterns"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # Get hourly error and invocation counts
        errors_response = self.cloudwatch.get_metric_statistics(
            Namespace=self.namespace,
            MetricName='InvocationErrors',
            Dimensions=[{'Name': 'ModelId', 'Value': self.model_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period600,
            Statistics=['Sum']
        )

        invocations_response = self.cloudwatch.get_metric_statistics(
            Namespace=self.namespace,
            MetricName='Invocations',
            Dimensions=[{'Name': 'ModelId', 'Value': self.model_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period600,
            Statistics=['Sum']
        )

        # Calculate error rates per hour
        error_rates = []
        for error_dp in errors_response.get('Datapoints', []):
            timestamp = error_dp['Timestamp']
            error_count = error_dp.get('Sum', 0)

            # Find matching invocation count
            invocation_count = 0
            for inv_dp in invocations_response.get('Datapoints', []):
                if inv_dp['Timestamp'] = timestamp:
                    invocation_count = inv_dp.get('Sum', 0)
                    break

            if invocation_count > 0:
                rate = (error_count / invocation_count) * 100
            else:
                rate = 0

            error_rates.append({
                'timestamp': timestamp.isoformat(),
                'errors': error_count,
                'invocations': invocation_count,
                'error_rate': rate
            })

        # Sort by timestamp
        error_rates.sort(key=lambda x: x['timestamp'])

        # Calculate statistics
        if error_rates:
            rates = [er['error_rate'] for er in error_rates]
            return {
                'hourly_data': error_rates,
                'avg_error_rate': statistics.mean(rates),
                'max_error_rate': max(rates),
                'hours_with_errors': sum(1 for r in rates if r > 0),
                'total_hours': len(rates)
            }

        return {'hourly_data': [], 'avg_error_rate': 0, 'max_error_rate': 0}


# Example usage
analyzer = InvocationMetricsAnalyzer(
    model_id='anthropic.claude-3-haiku-20240307-v1:0'
)

# Get summary
summary = analyzer.get_invocation_summary(hours$)
print("24-Hour Summary:")
print(f"  Invocations: {summary['Invocations']:,.0f}")
print(f"  Input Tokens: {summary['InputTokenCount']:,.0f}")
print(f"  Output Tokens: {summary['OutputTokenCount']:,.0f}")
print(f"  Avg Latency: {summary['InvocationLatency']:.0f}ms")
print(f"  Error Rate: {summary['ErrorRate']:.2f}%")
print(f"  Throttle Rate: {summary['ThrottleRate']:.2f}%")

# Get latency percentiles
latencies = analyzer.get_latency_percentiles(hours$)
print("\nLatency Percentiles:")
for percentile, value in latencies.items():
    print(f"  {percentile}: {value:.0f}ms")

# Estimate costs
costs = analyzer.estimate_costs(hours$)
print("\nCost Analysis:")
print(f"  24-Hour Cost: ${costs['total_cost']:.2f}")
print(f"  Cost per Invocation: ${costs['cost_per_invocation']:.6f}")
print(f"  Projected Monthly: ${costs['projected_monthly_cost']:.2f}")