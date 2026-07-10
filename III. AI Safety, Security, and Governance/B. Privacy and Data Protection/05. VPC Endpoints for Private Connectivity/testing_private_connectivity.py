import boto3
import socket

def verify_private_dns(service_name, region='us-east-1'):
    """
    Verify that DNS resolves to private IP addresses.
    """
    hostname = f'{service_name}.{region}.amazonaws.com'

    try:
        ip_addresses = socket.gethostbyname_ex(hostname)[2]
        print(f"DNS resolution for {hostname}:")

        for ip in ip_addresses:
            # Check if IP is private (10.x.x.x, 172.16-31.x.x, 192.168.x.x)
            is_private = (
                ip.startswith('10.') or
                ip.startswith('192.168.') or
                (ip.startswith('172.') and 16 <= int(ip.split('.')[1]) <= 31)
            )
            status = "PRIVATE" if is_private else "PUBLIC"
            print(f"  {ip} - {status}")

        return is_private
    except socket.gaierror as e:
        print(f"DNS resolution failed: {e}")
        return False

def test_bedrock_private_access():
    """
    Test Bedrock access via private endpoint.
    """
    bedrock = boto3.client('bedrock-runtime')

    try:
        # Simple test call
        response = bedrock.converse(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            messages=[
                {'role': 'user', 'content': [{'text': 'Say hello'}]}
            ],
            inferenceConfig={'maxTokens': 10}
        )
        print("Bedrock access successful via private endpoint")
        return True
    except Exception as e:
        print(f"Bedrock access failed: {e}")
        return False

# Verify DNS resolution
print("Checking DNS resolution...")
verify_private_dns('bedrock-runtime')

# Test actual access
print("\nTesting Bedrock access...")
test_bedrock_private_access()