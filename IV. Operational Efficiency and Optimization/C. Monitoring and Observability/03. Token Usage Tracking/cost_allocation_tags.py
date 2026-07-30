cloudwatch.put_metric_data(
    Namespace='GenAI/Costs',
    MetricData=[{
        'MetricName': 'TokenCost',
        'Dimensions': [
            {'Name': 'Team', 'Value': 'Marketing'},
            {'Name': 'Project', 'Value': 'Chatbot'},
            {'Name': 'Environment', 'Value': 'Production'}
        ],
        'Value': calculated_cost,
        'Unit': 'None'
    }]
)