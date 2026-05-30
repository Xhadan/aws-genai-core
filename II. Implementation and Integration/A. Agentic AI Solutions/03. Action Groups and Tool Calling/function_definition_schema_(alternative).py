# Alternative: Use function definitions instead of OpenAPI
response = bedrock_agent.create_agent_action_group(
    agentId='AGENT123',
    agentVersion='DRAFT',
    actionGroupName='calculator',
    description='Perform mathematical calculations',
    actionGroupExecutor={
        'lambda': 'arn:aws:lambda:us-east-1:123456789012:function:calculator'
    },
    functionSchema={
        'functions': [
            {
                'name': 'calculate',
                'description': 'Perform arithmetic calculation. Use for math questions.',
                'parameters': {
                    'expression': {
                        'type': 'string',
                        'description': 'Math expression to evaluate (e.g., "2 + 2 * 3")',
                        'required': True
                    }
                }
            },
            {
                'name': 'convert_units',
                'description': 'Convert between units of measurement',
                'parameters': {
                    'value': {
                        'type': 'number',
                        'description': 'Numeric value to convert',
                        'required': True
                    },
                    'from_unit': {
                        'type': 'string',
                        'description': 'Source unit (e.g., "miles", "kg")',
                        'required': True
                    },
                    'to_unit': {
                        'type': 'string',
                        'description': 'Target unit',
                        'required': True
                    }
                }
            }
        ]
    }
)