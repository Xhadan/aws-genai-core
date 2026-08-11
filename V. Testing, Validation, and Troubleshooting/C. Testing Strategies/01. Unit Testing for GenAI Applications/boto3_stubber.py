from botocore.stub import Stubber
import boto3

client = boto3.client('bedrock-runtime')
stubber = Stubber(client)

# Define expected response
response = {
    'output': {
        'message': {
            'content': [{'text': 'Mocked response'}]
        }
    }
}

stubber.add_response('converse', response)
stubber.activate()