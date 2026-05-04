import boto3

glue = boto3.client('glue')

# Create data quality ruleset
response = glue.create_data_quality_ruleset(
    Name='genai-training-data-rules',
    Description='Data quality rules for GenAI fine-tuning data',
    Ruleset='''
        Rules = [
            Completeness "prompt" >= 0.99,
            Completeness "completion" >= 0.99,
            ColumnLength "prompt" between 10 and 4096,
            ColumnLength "completion" between 5 and 2048,
            RowCount between 1000 and 1000000,
            IsUnique "id"
        ]
    ''',
    TargetTable={
        'TableName': 'training_data',
        'DatabaseName': 'genai_datasets'
    }
)

# Run data quality evaluation
run_response = glue.start_data_quality_ruleset_evaluation_run(
    DataSource={
        'GlueTable': {
            'DatabaseName': 'genai_datasets',
            'TableName': 'training_data'
        }
    },
    RulesetNames=['genai-training-data-rules']
)