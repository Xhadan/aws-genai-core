import boto3
import json
from typing import Dict

bedrock = boto3.client('bedrock')
bedrock_runtime = boto3.client('bedrock-runtime')

def create_safety_guardrail() -> str:
    """Create a guardrail for responsible AI content filtering."""

    response = bedrock.create_guardrail(
        name='ResponsibleAIGuardrail',
        description='Guardrail for safe, unbiased content generation',

        # Content policy filters
        contentPolicyConfig={
            'filtersConfig': [
                {'type': 'HATE', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                {'type': 'INSULTS', 'inputStrength': 'MEDIUM', 'outputStrength': 'HIGH'},
                {'type': 'SEXUAL', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                {'type': 'VIOLENCE', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                {'type': 'MISCONDUCT', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'}
            ]
        },

        # Sensitive information policy (PII)
        sensitiveInformationPolicyConfig={
            'piiEntitiesConfig': [
                {'type': 'EMAIL', 'action': 'BLOCK'},
                {'type': 'PHONE', 'action': 'ANONYMIZE'},
                {'type': 'SSN', 'action': 'BLOCK'},
                {'type': 'CREDIT_DEBIT_CARD_NUMBER', 'action': 'BLOCK'}
            ]
        },

        # Topic policy (block certain topics)
        topicPolicyConfig={
            'topicsConfig': [
                {
                    'name': 'illegal-activities',
                    'definition': 'Advice or instructions for illegal activities',
                    'examples': ['How to commit fraud', 'How to evade taxes illegally'],
                    'type': 'DENY'
                }
            ]
        },

        blockedInputMessaging='I cannot process this request due to content policy.',
        blockedOutputsMessaging='I cannot provide this response due to content policy.'
    )

    return response['guardrailId']

def invoke_with_guardrail(prompt: str, guardrail_id: str, guardrail_version: str = 'DRAFT') -> Dict:
    """Invoke model with guardrail protection."""

    response = bedrock_runtime.converse(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        messages=[{'role': 'user', 'content': [{'text': prompt}]}],
        guardrailConfig={
            'guardrailIdentifier': guardrail_id,
            'guardrailVersion': guardrail_version
        }
    )

    # Check guardrail action
    guardrail_result = {
        'blocked': False,
        'filters_triggered': [],
        'response': None
    }

    if response.get('stopReason') = 'guardrail_intervened':
        guardrail_result['blocked'] = True
        guardrail_result['filters_triggered'] = response.get('trace', {}).get('guardrail', {})
    else:
        guardrail_result['response'] = response['output']['message']['content'][0]['text']

    return guardrail_result

def evaluate_guardrail_effectiveness(test_prompts: list, guardrail_id: str) -> Dict:
    """Evaluate guardrail effectiveness on test prompts."""

    results = {
        'safe_prompts_passed': 0,
        'unsafe_prompts_blocked': 0,
        'false_positives': 0,
        'false_negatives': 0
    }

    for test in test_prompts:
        result = invoke_with_guardrail(test['prompt'], guardrail_id)

        if test['expected_safe']:
            if result['blocked']:
                results['false_positives'] += 1
            else:
                results['safe_prompts_passed'] += 1
        else:
            if result['blocked']:
                results['unsafe_prompts_blocked'] += 1
            else:
                results['false_negatives'] += 1

    total = len(test_prompts)
    results['accuracy'] = (results['safe_prompts_passed'] + results['unsafe_prompts_blocked']) / total

    return results