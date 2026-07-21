import boto3

bedrock = boto3.client('bedrock')

def create_provisioned_throughput(
    model_id,
    model_units,
    commitment_duration,
    throughput_name
):
    """
    Create provisioned throughput for consistent capacity.

    commitment_duration: 'OneMonth' or 'SixMonths' (or None for no commitment)
    """
    params = {
        'modelId': model_id,
        'modelUnits': model_units,
        'provisionedModelName': throughput_name
    }

    # Add commitment for discounted pricing
    if commitment_duration:
        params['commitmentDuration'] = commitment_duration

    response = bedrock.create_provisioned_model_throughput(**params)

    return response['provisionedModelArn']

def get_provisioned_throughput_status(provisioned_model_arn):
    """Check status of provisioned throughput"""
    response = bedrock.get_provisioned_model_throughput(
        provisionedModelId=provisioned_model_arn
    )

    return {
        'status': response['status'],
        'model_units': response['modelUnits'],
        'model_id': response['modelId'],
        'commitment': response.get('commitmentDuration', 'NoCommitment'),
        'commitment_expiration': response.get('commitmentExpirationTime')
    }

def list_provisioned_throughputs():
    """List all provisioned throughputs"""
    response = bedrock.list_provisioned_model_throughputs()

    throughputs = []
    for pt in response.get('provisionedModelSummaries', []):
        throughputs.append({
            'name': pt['provisionedModelName'],
            'arn': pt['provisionedModelArn'],
            'status': pt['status'],
            'model_id': pt['modelId'],
            'model_units': pt['modelUnits']
        })

    return throughputs

def update_provisioned_throughput(provisioned_model_arn, new_model_units):
    """Scale provisioned throughput up or down"""
    response = bedrock.update_provisioned_model_throughput(
        provisionedModelId=provisioned_model_arn,
        desiredModelUnits=new_model_units
    )
    return response

# Example: Create provisioned throughput with 6-month commitment
provisioned_arn = create_provisioned_throughput(
    model_id='anthropic.claude-3-sonnet-20240229-v1:0',
    model_units=1,
    commitment_duration='SixMonths',
    throughput_name='production-claude-sonnet'
)

print(f"Created provisioned throughput: {provisioned_arn}")

# Use provisioned throughput for inference
bedrock_runtime = boto3.client('bedrock-runtime')

response = bedrock_runtime.converse(
    modelId=provisioned_arn,  # Use ARN instead of model ID
    messages=[{'role': 'user', 'content': [{'text': 'Hello!'}]}]
)