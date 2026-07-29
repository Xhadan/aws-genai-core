import boto3
from datetime import datetime
from typing import Dict, List
import time

cloudwatch = boto3.client('cloudwatch')

class GenAICustomMetrics:
    """Publish custom GenAI metrics to CloudWatch"""

    def __init__(self, namespace: str = 'GenAI/Application'):
        self.cloudwatch = boto3.client('cloudwatch')
        self.namespace = namespace
        self.metric_buffer = []
        self.buffer_size = 20  # CloudWatch limit per PutMetricData call

    def record_invocation(
        self,
        model_id: str,
        prompt_tokens: int,
        response_tokens: int,
        latency_ms: float,
        cache_hit: bool = False,
        request_type: str = 'default'
    ):
        """Record comprehensive invocation metrics"""
        timestamp = datetime.utcnow()
        dimensions = [
            {'Name': 'ModelId', 'Value': model_id},
            {'Name': 'RequestType', 'Value': request_type}
        ]

        metrics = [
            {
                'MetricName': 'PromptTokens',
                'Dimensions': dimensions,
                'Timestamp': timestamp,
                'Value': prompt_tokens,
                'Unit': 'Count'
            },
            {
                'MetricName': 'ResponseTokens',
                'Dimensions': dimensions,
                'Timestamp': timestamp,
                'Value': response_tokens,
                'Unit': 'Count'
            },
            {
                'MetricName': 'TotalTokens',
                'Dimensions': dimensions,
                'Timestamp': timestamp,
                'Value': prompt_tokens + response_tokens,
                'Unit': 'Count'
            },
            {
                'MetricName': 'Latency',
                'Dimensions': dimensions,
                'Timestamp': timestamp,
                'Value': latency_ms,
                'Unit': 'Milliseconds'
            },
            {
                'MetricName': 'CacheHit',
                'Dimensions': dimensions,
                'Timestamp': timestamp,
                'Value': 1 if cache_hit else 0,
                'Unit': 'Count'
            }
        ]

        self.metric_buffer.extend(metrics)

        # Flush if buffer full
        if len(self.metric_buffer) >= self.buffer_size:
            self.flush_metrics()

    def record_quality_score(
        self,
        model_id: str,
        quality_score: float,
        relevance_score: float = None,
        coherence_score: float = None
    ):
        """Record response quality metrics"""
        timestamp = datetime.utcnow()
        dimensions = [{'Name': 'ModelId', 'Value': model_id}]

        metrics = [
            {
                'MetricName': 'QualityScore',
                'Dimensions': dimensions,
                'Timestamp': timestamp,
                'Value': quality_score,
                'Unit': 'None'
            }
        ]

        if relevance_score is not None:
            metrics.append({
                'MetricName': 'RelevanceScore',
                'Dimensions': dimensions,
                'Timestamp': timestamp,
                'Value': relevance_score,
                'Unit': 'None'
            })

        if coherence_score is not None:
            metrics.append({
                'MetricName': 'CoherenceScore',
                'Dimensions': dimensions,
                'Timestamp': timestamp,
                'Value': coherence_score,
                'Unit': 'None'
            })

        self.metric_buffer.extend(metrics)

    def record_cost(
        self,
        model_id: str,
        estimated_cost: float,
        cost_category: str = 'inference'
    ):
        """Record cost metrics"""
        self.metric_buffer.append({
            'MetricName': 'EstimatedCost',
            'Dimensions': [
                {'Name': 'ModelId', 'Value': model_id},
                {'Name': 'Category', 'Value': cost_category}
            ],
            'Timestamp': datetime.utcnow(),
            'Value': estimated_cost,
            'Unit': 'None'  # USD
        })

    def record_business_metric(
        self,
        metric_name: str,
        value: float,
        dimensions: Dict[str, str] = None,
        unit: str = 'Count'
    ):
        """Record arbitrary business metrics"""
        dims = [{'Name': k, 'Value': v} for k, v in (dimensions or {}).items()]

        self.metric_buffer.append({
            'MetricName': metric_name,
            'Dimensions': dims,
            'Timestamp': datetime.utcnow(),
            'Value': value,
            'Unit': unit
        })

    def flush_metrics(self):
        """Flush buffered metrics to CloudWatch"""
        if not self.metric_buffer:
            return

        # CloudWatch allows max 1000 metrics per call, 20 per batch for high-res
        for i in range(0, len(self.metric_buffer), self.buffer_size):
            batch = self.metric_buffer[i:i + self.buffer_size]
            try:
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricDatatch
                )
            except Exception as e:
                print(f"Failed to publish metrics: {e}")

        self.metric_buffer = []

    def __del__(self):
        """Flush remaining metrics on cleanup"""
        self.flush_metrics()


# Example: Instrument a GenAI application
metrics = GenAICustomMetrics(namespace='MyGenAIApp/Production')
bedrock = boto3.client('bedrock-runtime')

def invoke_with_metrics(prompt: str, model_id: str):
    """Invoke model with comprehensive metrics recording"""
    start_time = time.perf_counter()

    response = bedrock.converse(
        modelId=model_id,
        messages=[{'role': 'user', 'content': [{'text': prompt}]}],
        inferenceConfig={'maxTokens': 500}
    )

    latency_ms = (time.perf_counter() - start_time) * 1000
    usage = response.get('usage', {})

    # Record metrics
    metrics.record_invocation(
        model_id=model_id,
        prompt_tokens=usage.get('inputTokens', 0),
        response_tokens=usage.get('outputTokens', 0),
        latency_ms=latency_ms,
        request_type='chat'
    )

    # Estimate and record cost
    input_cost = (usage.get('inputTokens', 0) / 1000) * 0.00025
    output_cost = (usage.get('outputTokens', 0) / 1000) * 0.00125
    metrics.record_cost(model_id, input_cost + output_cost)

    # Record quality score (simulated)
    metrics.record_quality_score(
        model_id=model_id,
        quality_score=0.85  # In production, use actual quality evaluation
    )

    return response['output']['message']['content'][0]['text']

# Make invocations
response = invoke_with_metrics(
    prompt="What is AWS?",
    model_id='anthropic.claude-3-haiku-20240307-v1:0'
)

# Flush metrics
metrics.flush_metrics()