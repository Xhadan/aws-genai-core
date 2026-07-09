import boto3

ec2 = boto3.client('ec2')

def create_bedrock_endpoints(
    vpc_id,
    subnet_ids,
    security_group_id,
    region='us-east-1'
):
    """
    Create VPC endpoints for Amazon Bedrock services.
    """
    endpoints = []

    # Bedrock service endpoints
    bedrock_services = [
        f'com.amazonaws.{region}.bedrock',           # Control plane
        f'com.amazonaws.{region}.bedrock-runtime',   # Inference
        f'com.amazonaws.{region}.bedrock-agent-runtime'  # Agents
    ]

    for service_name in bedrock_services:
        response = ec2.create_vpc_endpoint(
            VpcId=vpc_id,
            ServiceName=service_name,
            VpcEndpointType='Interface',
            SubnetIds=subnet_ids,
            SecurityGroupIds=[security_group_id],
            PrivateDnsEnabled=True,  # Enable private DNS
            TagSpecifications=[
                {
                    'ResourceType': 'vpc-endpoint',
                    'Tags': [
                        {'Key': 'Name', 'Value': f'bedrock-endpoint-{service_name.split(".")[-1]}'},
                        {'Key': 'Environment', 'Value': 'production'}
                    ]
                }
            ]
        )
        endpoints.append({
            'service': service_name,
            'endpoint_id': response['VpcEndpoint']['VpcEndpointId'],
            'dns_entries': response['VpcEndpoint'].get('DnsEntries', [])
        })
        print(f"Created endpoint for {service_name}")

    return endpoints

# Create security group for endpoints
def create_endpoint_security_group(vpc_id, app_security_group_id):
    """
    Create security group for Bedrock VPC endpoints.
    """
    response = ec2.create_security_group(
        GroupName='bedrock-vpc-endpoints-sg',
        Description='Security group for Bedrock VPC endpoints',
        VpcId=vpc_id
    )
    sg_id = response['GroupId']

    # Allow HTTPS from application security group
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 443,
                'ToPort': 443,
                'UserIdGroupPairs': [
                    {'GroupId': app_security_group_id}
                ]
            }
        ]
    )

    print(f"Created security group: {sg_id}")
    return sg_id

# Example usage
vpc_id = 'vpc-12345678'
subnet_ids = ['subnet-11111111', 'subnet-22222222']  # Multiple AZs
app_sg = 'sg-application'

# Create endpoint security group
endpoint_sg = create_endpoint_security_group(vpc_id, app_sg)

# Create Bedrock endpoints
endpoints = create_bedrock_endpoints(
    vpc_id=vpc_id,
    subnet_ids=subnet_ids,
    security_group_id=endpoint_sg
)

for ep in endpoints:
    print(f"Service: {ep['service']}")
    print(f"  Endpoint ID: {ep['endpoint_id']}")