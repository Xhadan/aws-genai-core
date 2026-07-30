# Error rate > 5% for 3 periods
cloudwatch.put_metric_alarm(
    MetricName='error_rate',
    Expression='(errors/invocations)*100',
    Threshold=5.0,
    EvaluationPeriods=3
)