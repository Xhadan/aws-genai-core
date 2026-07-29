response = cloudwatch.get_metric_statistics(
    Namespace='AWS/Bedrock',
    MetricName='InputTokenCount',
    Dimensions=[{'Name': 'ModelId', 'Value': 'anthropic.claude-3-haiku-20240307-v1:0'}],
    StartTime=start_time,
    EndTime=end_time,
    Period600,
    Statistics=['Sum', 'Average']
)