import boto3

comprehend = boto3.client('comprehend')
bedrock_runtime = boto3.client('bedrock-runtime')

def enhanced_pii_detection(text):
    """
    Use Comprehend for detailed PII detection before Guardrails.
    Comprehend provides confidence scores and exact offsets.
    """
    # Comprehend PII detection
    comprehend_response = comprehend.detect_pii_entities(
        Text=text,
        LanguageCode='en'
    )

    pii_details = []
    for entity in comprehend_response['Entities']:
        pii_details.append({
            'type': entity['Type'],
            'score': entity['Score'],
            'begin_offset': entity['BeginOffset'],
            'end_offset': entity['EndOffset'],
            'text': text[entity['BeginOffset']:entity['EndOffset']]
        })

    return pii_details

def process_with_enhanced_detection(text, guardrail_id, guardrail_version):
    """
    First detect PII with Comprehend, then apply Guardrails.
    """
    # Step 1: Detailed PII detection
    pii_entities = enhanced_pii_detection(text)

    # Log high-confidence PII for audit
    high_confidence_pii = [p for p in pii_entities if p['score'] > 0.9]
    print(f"High-confidence PII detected: {len(high_confidence_pii)}")

    # Step 2: Apply Guardrails for action
    guardrail_response = bedrock_runtime.apply_guardrail(
        guardrailIdentifier=guardrail_id,
        guardrailVersion=guardrail_version,
        source='INPUT',
        content=[{'text': {'text': text}}]
    )

    return {
        'comprehend_pii': pii_entities,
        'guardrail_action': guardrail_response['action'],
        'safe_text': guardrail_response.get('outputs', [{}])[0].get('text')
    }