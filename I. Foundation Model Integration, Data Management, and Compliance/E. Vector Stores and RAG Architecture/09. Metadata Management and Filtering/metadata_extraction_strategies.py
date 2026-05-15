import boto3
import json
from datetime import datetime

def extract_document_metadata(s3_key, content):
    """
    Extract metadata from document content and path.
    """
    metadata = {}

    # Extract from S3 path
    path_parts = s3_key.split('/')
    if len(path_parts) > 1:
        metadata['source_folder'] = path_parts[0]
        metadata['filename'] = path_parts[-1]

    # Extract file type
    if '.' in s3_key:
        metadata['file_type'] = s3_key.rsplit('.', 1)[1].lower()

    # Add ingestion timestamp
    metadata['ingested_at'] = datetime.utcnow().isoformat()

    # Use Comprehend for entity/topic extraction
    comprehend = boto3.client('comprehend')

    # Extract entities
    entities_response = comprehend.detect_entities(
        Text=content[:5000],  # Comprehend limit
        LanguageCode='en'
    )
    metadata['entities'] = list(set([
        e['Text'] for e in entities_response['Entities']
        if e['Score'] > 0.8
    ]))

    # Extract key phrases
    phrases_response = comprehend.detect_key_phrases(
        Text=content[:5000],
        LanguageCode='en'
    )
    metadata['topics'] = [
        p['Text'] for p in phrases_response['KeyPhrases'][:10]
        if p['Score'] > 0.8
    ]

    # Detect language
    lang_response = comprehend.detect_dominant_language(Text=content[:1000])
    metadata['language'] = lang_response['Languages'][0]['LanguageCode']

    return metadata


def create_metadata_file(s3_bucket, document_key, metadata):
    """
    Create .metadata.json file for Bedrock Knowledge Base.
    """
    s3 = boto3.client('s3')

    metadata_content = {
        'metadataAttributes': {
            key: {
                'value': value,
                'type': infer_metadata_type(value)
            }
            for key, value in metadata.items()
        }
    }

    metadata_key = f"{document_key}.metadata.json"

    s3.put_object(
        Bucket=s3_bucket,
        Key=metadata_key,
        Body=json.dumps(metadata_content),
        ContentType='application/json'
    )


def infer_metadata_type(value):
    """Infer Bedrock metadata type from Python type."""
    if isinstance(value, bool):
        return 'BOOLEAN'
    elif isinstance(value, (int, float)):
        return 'NUMBER'
    elif isinstance(value, list):
        return 'STRING_LIST'
    else:
        return 'STRING'