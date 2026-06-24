from aws_cdk import (
    Stack,
    CustomResource,
    Duration,
    aws_lambda as lambda_,
    aws_iam as iam,
    custom_resources as cr,
)
from constructs import Construct

class ProvisionedThroughputConstruct(Construct):
    """Custom construct for Bedrock Provisioned Throughput (not in CloudFormation)."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        model_id: str,
        model_units: int,
        throughput_name: str,
        commitment_duration: str = "ONE_MONTH"
    ):
        super().__init__(scope, id)

        # Lambda function to manage provisioned throughput
        handler_code = """
import boto3
import json

bedrock = boto3.client('bedrock')

def on_event(event, context):
    request_type = event['RequestType']
    props = event['ResourceProperties']

    if request_type = 'Create':
        return create_throughput(props)
    elif request_type = 'Update':
        return update_throughput(event, props)
    elif request_type = 'Delete':
        return delete_throughput(event)

def create_throughput(props):
    response = bedrock.create_provisioned_model_throughput(
        modelUnits=int(props['ModelUnits']),
        provisionedModelName=props['ThroughputName'],
        modelId=props['ModelId'],
        commitmentDuration=props['CommitmentDuration']
    )
    return {
        'PhysicalResourceId': response['provisionedModelArn'],
        'Data': {
            'ProvisionedModelArn': response['provisionedModelArn']
        }
    }

def update_throughput(event, props):
    arn = event['PhysicalResourceId']
    bedrock.update_provisioned_model_throughput(
        provisionedModelId=arn,
        desiredModelUnits=int(props['ModelUnits'])
    )
    return {'PhysicalResourceId': arn}

def delete_throughput(event):
    arn = event['PhysicalResourceId']
    try:
        bedrock.delete_provisioned_model_throughput(provisionedModelId=arn)
    except bedrock.exceptions.ResourceNotFoundException:
        pass
    return {'PhysicalResourceId': arn}
"""

        # Create Lambda function
        handler = lambda_.Function(
            self, "Handler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_inline(handler_code),
            handler="index.on_event",
            timeout=Duration.minutes(5)
        )

        # Grant Bedrock permissions
        handler.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "bedrock:CreateProvisionedModelThroughput",
                "bedrock:UpdateProvisionedModelThroughput",
                "bedrock:DeleteProvisionedModelThroughput",
                "bedrock:GetProvisionedModelThroughput"
            ],
            resources=["*"]
        ))

        # Create provider
        provider = cr.Provider(
            self, "Provider",
            on_event_handler=handler
        )

        # Create custom resource
        self.resource = CustomResource(
            self, "Resource",
            service_token=provider.service_token,
            properties={
                "ModelId": model_id,
                "ModelUnits": str(model_units),
                "ThroughputName": throughput_name,
                "CommitmentDuration": commitment_duration
            }
        )

    @property
    def provisioned_model_arn(self) -> str:
        return self.resource.get_att_string("ProvisionedModelArn")


# Usage in stack
class MyStack(Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        throughput = ProvisionedThroughputConstruct(
            self, "ProvisionedThroughput",
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            model_units=2,
            throughput_name="prod-throughput",
            commitment_duration="ONE_MONTH"
        )

        # Use the ARN
        print(f"Provisioned ARN: {throughput.provisioned_model_arn}")