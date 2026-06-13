import boto3

bedrock = boto3.client('bedrock')

def list_provisioned_throughputs():
    """List all provisioned throughputs in the account."""
    response = bedrock.list_provisioned_model_throughputs()

    for pt in response['provisionedModelSummaries']:
        print(f"Name: {pt['provisionedModelName']}")
        print(f"  Status: {pt['status']}")
        print(f"  Model Units: {pt['modelUnits']}")
        print(f"  Commitment: {pt.get('commitmentDuration', 'N/A')}")
        print(f"  Expires: {pt.get('commitmentExpirationTime', 'N/A')}")
        print()

    return response['provisionedModelSummaries']

def update_provisioned_throughput(provisioned_arn: str, new_model_units: int):
    """Update the model units for a provisioned throughput."""
    response = bedrock.update_provisioned_model_throughput(
        provisionedModelId=provisioned_arn,
        desiredModelUnits=new_model_units
    )
    return response

def delete_provisioned_throughput(provisioned_arn: str):
    """
    Delete provisioned throughput.
    Note: Cannot delete before commitment period ends without penalty.
    """
    response = bedrock.delete_provisioned_model_throughput(
        provisionedModelId=provisioned_arn
    )
    return response

# List current provisioned throughputs
throughputs = list_provisioned_throughputs()