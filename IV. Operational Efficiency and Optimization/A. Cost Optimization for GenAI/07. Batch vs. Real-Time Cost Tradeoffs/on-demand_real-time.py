response = bedrock_runtime.converse(
    modelId='anthropic.claude-3-haiku-20240307-v1:0',
    messages=[{'role': 'user', 'content': [{'text': prompt}]}]
)
# Response available immediately