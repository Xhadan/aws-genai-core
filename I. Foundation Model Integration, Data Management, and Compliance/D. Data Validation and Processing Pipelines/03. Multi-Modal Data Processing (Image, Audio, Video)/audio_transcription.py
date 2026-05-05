import boto3

transcribe = boto3.client('transcribe')

def transcribe_audio(bucket, audio_key, language='en-US'):
    """Transcribe audio file for GenAI processing."""
    job_name = f"transcribe-{audio_key.replace('/', '-')}"

    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': f's3://{bucket}/{audio_key}'},
        MediaFormat='mp3',
        LanguageCode=language,
        OutputBucketName=bucket,
        OutputKey=f'transcripts/{job_name}.json'
    )

    # Wait for completion and retrieve transcript
    while True:
        result = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if result['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break

    return result['TranscriptionJob']['Transcript']['TranscriptFileUri']