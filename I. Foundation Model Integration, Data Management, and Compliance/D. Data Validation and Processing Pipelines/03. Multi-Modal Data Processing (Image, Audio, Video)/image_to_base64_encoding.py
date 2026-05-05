import base64
import boto3
from PIL import Image
import io

def prepare_image(image_path, max_size=(1568, 1568)):
    """Resize and encode image for Bedrock API."""
    with Image.open(image_path) as img:
        # Resize if too large
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Encode to base64
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality)
        encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return encoded

# Use with Bedrock
bedrock = boto3.client('bedrock-runtime')
image_data = prepare_image('document.png')

response = bedrock.invoke_model(
    modelId='anthropic.claude-3-sonnet-20240229-v1:0',
    body={
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
                {"type": "text", "text": "Describe this image in detail."}
            ]
        }],
        "max_tokens": 1024
    }
)