import boto3
from sagemaker import ModelPackage

sm_client = boto3.client('sagemaker')

# Define deployment configuration with canary
deployment_config = {
    'BlueGreenUpdatePolicy': {
        'TrafficRoutingConfiguration': {
            'Type': 'CANARY',
            'CanarySize': {
                'Type': 'CAPACITY_PERCENT',
                'Value': 25  # 25% of green fleet receives canary traffic
            },
            'WaitIntervalInSeconds': 600  # 10-minute baking period
        },
        'TerminationWaitInSeconds': 300,  # Wait before terminating blue
        'MaximumExecutionTimeoutInSeconds': 3600  # Max deployment time
    },
    'AutoRollbackConfiguration': {
        'Alarms': [
            {'AlarmName': 'genai-endpoint-5xx-alarm'},
            {'AlarmName': 'genai-endpoint-latency-alarm'},
            {'AlarmName': 'genai-model-error-rate-alarm'}
        ]
    }
}

# Update endpoint with canary deployment
sm_client.update_endpoint(
    EndpointName='genai-production-endpoint',
    EndpointConfigName='genai-endpoint-config-v2',
    DeploymentConfigployment_config,
    RetainDeploymentConfig=True
)