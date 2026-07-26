response = bedrock_runtime.converse_stream(
    modelId='anthropic.claude-3-haiku-20240307-v1:0',
    messages=[{'role': 'user', 'content': [{'text': prompt}]}]
)

for event in response['stream']:
    if 'contentBlockDelta' in event:
        print(event['contentBlockDelta']['delta']['text'], end='')