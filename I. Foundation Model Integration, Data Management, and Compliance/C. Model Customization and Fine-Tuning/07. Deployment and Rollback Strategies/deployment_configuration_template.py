deployment_config = {
    'BlueGreenUpdatePolicy': {
        'TrafficRoutingConfiguration': {
            'Type': 'CANARY',  # or 'LINEAR', 'ALL_AT_ONCE'
            'CanarySize': {
                'Type': 'CAPACITY_PERCENT',
                'Value': 10  # Start with 10%
            },
            'WaitIntervalInSeconds': 900  # 15-minute bake
        },
        'TerminationWaitInSeconds': 600,
        'MaximumExecutionTimeoutInSeconds': 7200
    },
    'AutoRollbackConfiguration': {
        'Alarms': [
            {'AlarmName': 'endpoint-5xx-alarm'},
            {'AlarmName': 'endpoint-p99-latency-alarm'},
            {'AlarmName': 'model-quality-alarm'}
        ]
    }
}