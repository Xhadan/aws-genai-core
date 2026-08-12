import boto3
from botocore.stub import Stubber
import pytest
from typing import Dict

class BedrockClient:
    """Wrapper for Bedrock API calls."""

    def __init__(self, client=None):
        self.client = client or boto3.client('bedrock-runtime')

    def generate_response(self, prompt: str) -> str:
        """Generate response from Bedrock model."""
        response = self.client.converse(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            messages=[{'role': 'user', 'content': [{'text': prompt}]}]
        )
        return response['output']['message']['content'][0]['text']

# Test file
class TestBedrockClient:

    @pytest.fixture
    def mock_client(self):
        """Create stubbed Bedrock client."""
        client = boto3.client('bedrock-runtime', region_name='us-east-1')
        stubber = Stubber(client)
        return client, stubber

    def test_generate_response_success(self, mock_client):
        """Test successful response generation."""
        client, stubber = mock_client

        # Define expected response
        expected_response = {
            'output': {
                'message': {
                    'role': 'assistant',
                    'content': [{'text': 'This is a mocked response'}]
                }
            },
            'stopReason': 'end_turn',
            'usage': {'inputTokens': 10, 'outputTokens': 20}
        }

        # Expected request parameters
        expected_params = {
            'modelId': 'anthropic.claude-3-sonnet-20240229-v1:0',
            'messages': [{'role': 'user', 'content': [{'text': 'Test prompt'}]}]
        }

        stubber.add_response('converse', expected_response, expected_params)
        stubber.activate()

        # Execute test
        bedrock = BedrockClient(client)
        result = bedrock.generate_response('Test prompt')

        assert result = 'This is a mocked response'
        stubber.assert_no_pending_responses()

    def test_generate_response_error(self, mock_client):
        """Test error handling."""
        client, stubber = mock_client

        stubber.add_client_error(
            'converse',
            service_error_code='ThrottlingException',
            service_message='Rate exceeded'
        )
        stubber.activate()

        bedrock = BedrockClient(client)

        with pytest.raises(Exception) as exc_info:
            bedrock.generate_response('Test prompt')

        assert 'ThrottlingException' in str(exc_info.value)