import boto3
import json
import base64

bedrock = boto3.client('bedrock-runtime')

def generate_image(prompt, negative_prompt=None):
    """Generate image from text prompt."""
    body = {
        'taskType': 'TEXT_IMAGE',
        'textToImageParams': {
            'text': prompt
        },
        'imageGenerationConfig': {
            'numberOfImages': 1,
            'height': 1024,
            'width': 1024,
            'cfgScale': 8.0,
            'seed': 0  # 0 for random
        }
    }

    if negative_prompt:
        body['textToImageParams']['negativeText'] = negative_prompt

    response = bedrock.invoke_model(
        modelId='amazon.titan-image-generator-v1',
        body=json.dumps(body)
    )

    result = json.loads(response['body'].read())
    # Returns base64-encoded image
    return result['images'][0]

# Generate product image
image_b64 = generate_image(
    prompt="Professional product photo of a red sports car, studio lighting, white background",
    negative_prompt="blurry, low quality, distorted"
)