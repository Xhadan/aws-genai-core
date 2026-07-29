# Enable X-Ray tracing for Bedrock calls
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
patch_all()  # Patches boto3 for X-Ray