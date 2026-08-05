import boto3

events = boto3.client('events')
sfn = boto3.client('stepfunctions')

# Create scheduled evaluation rule
events.put_rule(
    Name='DailyModelEvaluation',
    ScheduleExpression='cron(0 2 * * ? *)',  # 2 AM UTC daily
    State='ENABLED',
    Description='Trigger daily model evaluation pipeline'
)

# Add Step Functions as target
events.put_targets(
    Rule='DailyModelEvaluation',
    Targets=[
        {
            'Id': 'EvaluationPipeline',
            'Arn': 'arn:aws:states:us-east-1:123456789012:stateMachine:EvalPipeline',
            'RoleArn': 'arn:aws:iam::123456789012:role/EventBridgeStepFunctionsRole',
            'Input': json.dumps({
                'dataset_s3_uri': 's3://my-bucket/eval-data/daily-test.jsonl',
                'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
                'evaluation_type': 'daily_regression'
            })
        }
    ]
)

# Create deployment-triggered evaluation
events.put_rule(
    Name='DeploymentEvaluation',
    EventPattern=json.dumps({
        'source': ['aws.codepipeline'],
        'detail-type': ['CodePipeline Stage Execution State Change'],
        'detail': {
            'stage': ['Deploy'],
            'state': ['STARTED']
        }
    }),
    State='ENABLED',
    Description='Trigger evaluation on deployment'
)

# Add target for deployment events
events.put_targets(
    Rule='DeploymentEvaluation',
    Targets=[
        {
            'Id': 'DeploymentEvalPipeline',
            'Arn': 'arn:aws:states:us-east-1:123456789012:stateMachine:EvalPipeline',
            'RoleArn': 'arn:aws:iam::123456789012:role/EventBridgeStepFunctionsRole',
            'InputTransformer': {
                'InputPathsMap': {
                    'pipeline': '$.detail.pipeline',
                    'stage': '$.detail.stage'
                },
                'InputTemplate': '{"dataset_s3_uri": "s3://my-bucket/eval-data/pre-deploy.jsonl", "triggered_by": "<pipeline>", "evaluation_type": "pre_deployment"}'
            }
        }
    ]
)