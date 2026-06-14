import boto3

def configure_autoscaling(
    endpoint_name: str,
    variant_name: str = "AllTraffic",
    min_capacity: int = 1,
    max_capacity: int = 4
):
    """Configure auto-scaling for a real-time endpoint."""

    client = boto3.client('application-autoscaling')

    # Register scalable target
    resource_id = f"endpoint/{endpoint_name}/variant/{variant_name}"

    client.register_scalable_target(
        ServiceNamespace='sagemaker',
        ResourceId=resource_id,
        ScalableDimension='sagemaker:variant:DesiredInstanceCount',
        MinCapacity=min_capacity,
        MaxCapacity=max_capacity
    )

    # Create scaling policy based on invocations per instance
    client.put_scaling_policy(
        PolicyName=f"{endpoint_name}-scaling-policy",
        ServiceNamespace='sagemaker',
        ResourceId=resource_id,
        ScalableDimension='sagemaker:variant:DesiredInstanceCount',
        PolicyType='TargetTrackingScaling',
        TargetTrackingScalingPolicyConfiguration={
            'TargetValue': 70.0,  # Target 70% utilization
            'PredefinedMetricSpecification': {
                'PredefinedMetricType': 'SageMakerVariantInvocationsPerInstance'
            },
            'ScaleInCooldown': 300,
            'ScaleOutCooldown': 60
        }
    )

    print(f"Auto-scaling configured: {min_capacity}-{max_capacity} instances")