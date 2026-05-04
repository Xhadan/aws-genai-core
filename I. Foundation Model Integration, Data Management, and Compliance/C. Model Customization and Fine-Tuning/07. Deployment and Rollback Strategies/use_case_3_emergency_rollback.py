# Rollback to previous endpoint configuration
sm_client.update_endpoint(
    EndpointName='genai-production-endpoint',
    EndpointConfigName='genai-endpoint-config-v1-stable',  # Previous known good
    DeploymentConfig={
        'BlueGreenUpdatePolicy': {
            'TrafficRoutingConfiguration': {
                'Type': 'ALL_AT_ONCE',  # Immediate for emergency
                'WaitIntervalInSeconds': 0
            }
        }
    }
)