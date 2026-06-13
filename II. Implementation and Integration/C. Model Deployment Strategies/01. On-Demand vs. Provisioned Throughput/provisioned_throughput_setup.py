import boto3

bedrock = boto3.client('bedrock')

def create_provisioned_throughput(
    model_id: str,
    model_units: int,
    throughput_name: str,
    commitment_duration: str = "ONE_MONTH"
):
    """
    Create Provisioned Throughput for dedicated capacity.

    Args:
        model_id: Base model ARN
        model_units: Number of model units to provision
        throughput_name: Unique name for this provisioned throughput
        commitment_duration: ONE_MONTH or SIX_MONTHS
    """
    response = bedrock.create_provisioned_model_throughput(
        modelUnits=model_units,
        provisionedModelName=throughput_name,
        modelId=model_id,
        commitmentDuration=commitment_duration,
        tags=[
            {'key': 'Environment', 'value': 'Production'},
            {'key': 'Application', 'value': 'CustomerService'}
        ]
    )

    provisioned_arn = response['provisionedModelArn']
    print(f"Provisioned Throughput ARN: {provisioned_arn}")

    return provisioned_arn

# Create provisioned throughput for Claude
provisioned_arn = create_provisioned_throughput(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    model_units=2,
    throughput_name="prod-customer-service-claude",
    commitment_duration="ONE_MONTH"
)