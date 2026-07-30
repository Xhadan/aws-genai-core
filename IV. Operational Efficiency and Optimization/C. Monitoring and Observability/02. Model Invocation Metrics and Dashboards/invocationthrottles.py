# Any throttling indicates potential issues
cloudwatch.put_metric_alarm(
    MetricName='InvocationThrottles',
    Statistic='Sum',
    Threshold=0,
    ComparisonOperator='GreaterThanThreshold'
)