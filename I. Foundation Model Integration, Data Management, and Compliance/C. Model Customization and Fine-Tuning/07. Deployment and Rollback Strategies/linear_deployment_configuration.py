deployment_config = {
    'BlueGreenUpdatePolicy': {
        'TrafficRoutingConfiguration': {
            'Type': 'LINEAR',
            'LinearStepSize': {
                'Type': 'CAPACITY_PERCENT',
                'Value': 10  # Increase by 10% each step
            },
            'WaitIntervalInSeconds': 300  # 5 min between steps
        },
        'AutoRollbackConfiguration': {
            'Alarms': [
                {'AlarmName': 'genai-endpoint-5xx-alarm'},
                {'AlarmName': 'genai-endpoint-latency-alarm'}
            ]
        }
    }
}

# Traffic shifts: 10% → 20% → 30% → ... → 100%
# Each step waits 5 minutes for baking