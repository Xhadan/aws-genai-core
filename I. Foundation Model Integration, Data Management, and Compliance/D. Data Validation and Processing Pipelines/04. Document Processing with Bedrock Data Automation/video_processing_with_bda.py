# Process video for content extraction
response = bedrock_data.invoke_data_automation_async(
    inputConfiguration={
        'video': {
            's3Uri': 's3://my-bucket/videos/training-video.mp4'
        }
    },
    outputConfiguration={
        's3Uri': 's3://my-bucket/video-output/',
        'format': 'JSON'
    },
    dataAutomationConfiguration={
        'video': {
            'extractionTypes': ['TRANSCRIPT', 'SCENE', 'VISUAL_SUMMARY'],
            'transcriptConfiguration': {
                'languageCode': 'en-US',
                'includeTimestamps': True
            }
        }
    }
)