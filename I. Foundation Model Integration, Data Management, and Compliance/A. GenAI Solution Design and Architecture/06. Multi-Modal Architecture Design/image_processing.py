import boto3
import base64

bedrock = boto3.client('bedrock-runtime')

# Read and encode image
with open('document.png', 'rb') as f:
    image_data = base64.standard_b64encode(f.read()).decode('utf-8')

response = bedrock.converse(
    modelId='anthropic.claude-3-sonnet-20240229-v1:0',
    messages=[
        {
            'role': 'user',
            'content': [
                {
                    'image': {
                        'format': 'png',
                        'source': {'bytes': base64.b64decode(image_data)}
                    }
                },
                {
                    'text': 'Extract all text from this document and summarize the key points.'
                }
            ]
        }
    ]
)

print(response['output']['message']['content'][0]['text'])