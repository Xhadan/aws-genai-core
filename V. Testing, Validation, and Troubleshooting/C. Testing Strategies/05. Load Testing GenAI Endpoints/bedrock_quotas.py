import boto3

service_quotas = boto3.client('service-quotas')

response = service_quotas.get_service_quota(
    ServiceCode='bedrock',
    QuotaCode='L-XXXXXXXX'  # Model-specific quota code
)

print(f"TPM Limit: {response['Quota']['Value']}")