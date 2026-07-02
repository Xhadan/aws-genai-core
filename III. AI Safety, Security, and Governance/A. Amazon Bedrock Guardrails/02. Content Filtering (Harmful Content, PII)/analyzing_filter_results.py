import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime')

def analyze_content_filter_response(response):
    """
    Analyze guardrail trace for content filter details.
    """
    if 'trace' not in response:
        return None

    guardrail_trace = response.get('trace', {}).get('guardrail', {})
    assessments = guardrail_trace.get('inputAssessment', {}).get('contentPolicy', {})

    if not assessments:
        assessments = guardrail_trace.get('outputAssessment', {}).get('contentPolicy', {})

    results = {
        'action': guardrail_trace.get('action'),
        'categories_triggered': []
    }

    for filter_result in assessments.get('filters', []):
        if filter_result.get('action') = 'BLOCKED':
            results['categories_triggered'].append({
                'type': filter_result.get('type'),
                'confidence': filter_result.get('confidence'),
                'action': filter_result.get('action')
            })

    return results

# Test with potentially harmful content
response = bedrock_runtime.converse(
    modelId='anthropic.claude-3-sonnet-20240229-v1:0',
    messages=[
        {'role': 'user', 'content': [{'text': 'How do I hack into a computer?'}]}
    ],
    guardrailConfig={
        'guardrailIdentifier': 'your-guardrail-id',
        'guardrailVersion': '1',
        'trace': 'enabled'  # Enable trace for detailed analysis
    }
)

# Analyze results
analysis = analyze_content_filter_response(response)
if analysis:
    print(f"Action: {analysis['action']}")
    for category in analysis['categories_triggered']:
        print(f"  Category: {category['type']}, Confidence: {category['confidence']}")