import boto3

transcribe = boto3.client('transcribe')
bedrock = boto3.client('bedrock-runtime')
polly = boto3.client('polly')

def process_voice_query(audio_file_uri):
    # Step 1: Transcribe audio to text
    transcribe.start_transcription_job(
        TranscriptionJobName='voice-query',
        Media={'MediaFileUri': audio_file_uri},
        MediaFormat='wav',
        LanguageCode='en-US'
    )
    # ... wait for completion and get transcript ...
    transcript = "User's spoken question here"

    # Step 2: Process with Bedrock
    response = bedrock.converse(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        messages=[{'role': 'user', 'content': [{'text': transcript}]}]
    )
    answer = response['output']['message']['content'][0]['text']

    # Step 3: Convert response to speech
    polly_response = polly.synthesize_speech(
        Text=answer,
        OutputFormat='mp3',
        VoiceId='Joanna',
        Engine='neural'
    )

    return polly_response['AudioStream'].read()