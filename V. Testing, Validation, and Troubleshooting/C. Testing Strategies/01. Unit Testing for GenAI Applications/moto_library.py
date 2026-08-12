from moto import mock_bedrock_runtime

@mock_bedrock_runtime
def test_bedrock_call():
    client = boto3.client('bedrock-runtime')
    # Test code using mocked service