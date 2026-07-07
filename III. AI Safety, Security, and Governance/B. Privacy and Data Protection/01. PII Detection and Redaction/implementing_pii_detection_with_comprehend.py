import boto3

comprehend = boto3.client('comprehend')

def detect_pii_detailed(text, language='en'):
    """
    Detect PII with confidence scores and positions.
    """
    response = comprehend.detect_pii_entities(
        Text=text,
        LanguageCode=language
    )

    pii_entities = []
    for entity in response['Entities']:
        pii_entities.append({
            'type': entity['Type'],
            'score': entity['Score'],
            'begin': entity['BeginOffset'],
            'end': entity['EndOffset'],
            'text': text[entity['BeginOffset']:entity['EndOffset']]
        })

    return pii_entities

def redact_pii(text, entities, replacement_style='placeholder'):
    """
    Redact PII from text using detected entities.
    """
    # Sort by position (reverse) to maintain offsets during replacement
    sorted_entities = sorted(entities, key=lambda x: x['begin'], reverse=True)

    redacted_text = text
    for entity in sorted_entities:
        if replacement_style = 'placeholder':
            replacement = f"{{{entity['type']}}}"
        elif replacement_style = 'mask':
            replacement = '*' * (entity['end'] - entity['begin'])
        else:
            replacement = '[REDACTED]'

        redacted_text = (
            redacted_text[:entity['begin']] +
            replacement +
            redacted_text[entity['end']:]
        )

    return redacted_text

# Example usage
text = """
Hello, I'm John Smith and my email is john.smith@example.com.
My SSN is 123-45-6789 and I live at 123 Main St, Seattle, WA 98101.
Please call me at (555) 123-4567.
"""

# Detect PII
entities = detect_pii_detailed(text)
print("Detected PII:")
for entity in entities:
    print(f"  {entity['type']}: '{entity['text']}' (confidence: {entity['score']:.2f})")

# Redact with different styles
print("\n--- Placeholder redaction ---")
print(redact_pii(text, entities, 'placeholder'))

print("\n--- Masked redaction ---")
print(redact_pii(text, entities, 'mask'))