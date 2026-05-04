import boto3

cloudwatch = boto3.client('cloudwatch')

# 5xx Error Rate Alarm
cloudwatch.put_metric_alarm(
    AlarmName='genai-endpoint-5xx-alarm',
    AlarmDescription='Alarm when 5xx errors exceed threshold',
    MetricName='Invocation5XXErrors',
    Namespace='AWS/SageMaker',
    Dimensions=[
        {'Name': 'EndpointName', 'Value': 'genai-production-endpoint'},
        {'Name': 'VariantName', 'Value': 'AllTraffic'}
    ],
    Statistic='Sum',
    Period`,
    EvaluationPeriods=2,
    Threshold,
    ComparisonOperator='GreaterThanThreshold',
    TreatMissingData='notBreaching'
)

# Latency Alarm (P99)
cloudwatch.put_metric_alarm(
    AlarmName='genai-endpoint-latency-alarm',
    AlarmDescription='Alarm when P99 latency exceeds threshold',
    MetricName='ModelLatency',
    Namespace='AWS/SageMaker',
    Dimensions=[
        {'Name': 'EndpointName', 'Value': 'genai-production-endpoint'},
        {'Name': 'VariantName', 'Value': 'AllTraffic'}
    ],
    ExtendedStatistic='p99',
    Period`,
    EvaluationPeriods=3,
    ThresholdP00000,  # 5 seconds in microseconds
    ComparisonOperator='GreaterThanThreshold'
)