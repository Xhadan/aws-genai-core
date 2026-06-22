import boto3
import json

scheduler = boto3.client('scheduler')

def create_scheduled_genai_tasks():
    """Create scheduled tasks for periodic GenAI operations."""

    # Daily report generation
    scheduler.create_schedule(
        Name='daily-summary-report',
        ScheduleExpression='cron(0 8 * * ? *)',  # 8 AM UTC daily
        FlexibleTimeWindow={'Mode': 'OFF'},
        Target={
            'Arn': 'arn:aws:lambda:us-east-1:123456789012:function:generate-daily-report',
            'RoleArn': 'arn:aws:iam::123456789012:role/scheduler-role',
            'Input': json.dumps({
                'report_type': 'daily_summary',
                'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0'
            })
        },
        Description='Generate daily AI summary report'
    )

    # Hourly sentiment analysis
    scheduler.create_schedule(
        Name='hourly-sentiment-analysis',
        ScheduleExpression='rate(1 hour)',
        FlexibleTimeWindow={'Mode': 'FLEXIBLE', 'MaximumWindowInMinutes': 15},
        Target={
            'Arn': 'arn:aws:lambda:us-east-1:123456789012:function:batch-sentiment-analysis',
            'RoleArn': 'arn:aws:iam::123456789012:role/scheduler-role',
            'Input': json.dumps({
                'source': 'support_tickets',
                'lookback_hours': 1
            })
        },
        Description='Hourly batch sentiment analysis of support tickets'
    )

    # Weekly content refresh
    scheduler.create_schedule(
        Name='weekly-content-refresh',
        ScheduleExpression='cron(0 2 ? * SUN *)',  # 2 AM UTC every Sunday
        FlexibleTimeWindow={'Mode': 'OFF'},
        Target={
            'Arn': 'arn:aws:states:us-east-1:123456789012:stateMachine:content-refresh',
            'RoleArn': 'arn:aws:iam::123456789012:role/scheduler-role',
            'Input': json.dumps({
                'refresh_type': 'full',
                'categories': ['products', 'faq', 'blog']
            })
        },
        Description='Weekly AI content refresh'
    )

    print("Scheduled tasks created")

# Lambda handler for scheduled report
def generate_daily_report_handler(event, context):
    """Generate daily summary report using GenAI."""
    import boto3

    bedrock = boto3.client('bedrock-runtime')
    dynamodb = boto3.resource('dynamodb')

    # Gather metrics from previous day
    metrics = gather_daily_metrics()

    # Generate AI summary
    response = bedrock.invoke_model(
        modelId=event.get('model_id', 'anthropic.claude-3-sonnet-20240229-v1:0'),
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [{
                "role": "user",
                "content": f"""Generate an executive summary report based on these metrics:

{json.dumps(metrics, indent=2)}

Include:
1. Key highlights
2. Trends and patterns
3. Recommendations
4. Areas of concern"""
            }]
        })
    )

    result = json.loads(response['body'].read())
    report = result['content'][0]['text']

    # Store report
    reports_table = dynamodb.Table('daily-reports')
    reports_table.put_item(Item={
        'report_date': event.get('date', datetime.utcnow().strftime('%Y-%m-%d')),
        'report_content': report,
        'metrics': metrics,
        'generated_at': datetime.utcnow().isoformat()
    })

    return {'status': 'completed', 'report_length': len(report)}

def gather_daily_metrics():
    """Placeholder for metrics gathering."""
    return {
        'total_requests': 15000,
        'successful_requests': 14850,
        'average_latency_ms': 1200,
        'total_tokens': 5000000,
        'top_models': ['claude-3-sonnet', 'claude-3-haiku']
    }