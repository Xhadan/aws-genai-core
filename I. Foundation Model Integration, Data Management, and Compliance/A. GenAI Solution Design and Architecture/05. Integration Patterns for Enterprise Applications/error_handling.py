import time
from botocore.config import Config

config = Config(
    retries={
        'max_attempts': 3,
        'mode': 'adaptive'  # Exponential backoff
    }
)
bedrock = boto3.client('bedrock-runtime', config=config)