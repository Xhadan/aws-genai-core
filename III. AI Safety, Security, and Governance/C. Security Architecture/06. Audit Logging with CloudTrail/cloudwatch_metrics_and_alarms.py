import boto3

cloudwatch = boto3.client('cloudwatch')
logs = boto3.client('logs')

def create_guardrail_deletion_alarm():
    """
    Alert when guardrails are deleted.
    """
    # Create metric filter from CloudTrail logs
    logs.put_metric_filter(
        logGroupName='/aws/cloudtrail/my-trail',
        filterName='GuardrailDeletionFilter',
        filterPattern='{ ($.eventSource = "bedrock.amazonaws.com") && ($.eventName = "DeleteGuardrail") }',
        metricTransformations=[
            {
                'metricName': 'GuardrailDeletions',
                'metricNamespace': 'Bedrock/Security',
                'metricValue': '1'
            }
        ]
    )

    # Create alarm
    cloudwatch.put_metric_alarm(
        AlarmName='Bedrock-Guardrail-Deletion',
        MetricName='GuardrailDeletions',
        Namespace='Bedrock/Security',
        Statistic='Sum',
        Period00,  # 5 minutes
        EvaluationPeriods=1,
        Threshold=1,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        AlarmDescription='Alert when a Bedrock guardrail is deleted',
        AlarmActions=[
            'arn:aws:sns:us-east-1:123456789012:security-alerts'
        ]
    )
    print("Guardrail deletion alarm created")

def create_high_invocation_alarm():
    """
    Alert on unusually high model invocation rates.
    """
    cloudwatch.put_metric_alarm(
        AlarmName='Bedrock-High-Invocation-Rate',
        MetricName='Invocations',
        Namespace='AWS/Bedrock',
        Statistic='Sum',
        Period00,
        EvaluationPeriods=2,
        Threshold000,  # Adjust based on baseline
        ComparisonOperator='GreaterThanThreshold',
        AlarmDescription='Alert on unusual invocation spike',
        AlarmActions=[
            'arn:aws:sns:us-east-1:123456789012:security-alerts'
        ]
    )
    print("High invocation alarm created")

create_guardrail_deletion_alarm()
create_high_invocation_alarm()