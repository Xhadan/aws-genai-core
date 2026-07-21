response = bedrock_runtime.converse(
    modelId='anthropic.claude-3-haiku-20240307-v1:0',
    messages=messages,
    inferenceConfig={
        'maxTokens': 100,  # Hard limit
        'stopSequences': ['\n\n']  # Stop at paragraph break
    }
)