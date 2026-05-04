# Create endpoint config with shadow variant
endpoint_config = {
    'ProductionVariants': [
        {
            'VariantName': 'production',
            'ModelName': 'genai-model-v1',
            'InstanceType': 'ml.g5.xlarge',
            'InitialInstanceCount': 2,
            'InitialVariantWeight': 1.0  # All traffic
        }
    ],
    'ShadowProductionVariants': [
        {
            'VariantName': 'shadow-v2',
            'ModelName': 'genai-model-v2',
            'InstanceType': 'ml.g5.xlarge',
            'InitialInstanceCount': 1,
            'InitialVariantWeight': 1.0  # Receives copy of all requests
        }
    ],
    'DataCaptureConfig': {
        'EnableCapture': True,
        'CaptureOptions': [
            {'CaptureMode': 'Input'},
            {'CaptureMode': 'Output'}
        ],
        'DestinationS3Uri': 's3://my-bucket/shadow-captures/'
    }
}

# Shadow receives all requests but responses not returned to users
# Compare outputs offline for validation