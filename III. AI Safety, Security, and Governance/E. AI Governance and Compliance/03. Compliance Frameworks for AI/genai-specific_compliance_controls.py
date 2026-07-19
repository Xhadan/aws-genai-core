import boto3
import json

bedrock = boto3.client('bedrock')
bedrock_runtime = boto3.client('bedrock-runtime')

def create_compliant_guardrail(framework, guardrail_name):
    """
    Create Bedrock Guardrail with compliance-appropriate settings.
    """
    # Base configuration
    config = {
        'name': guardrail_name,
        'description': f'Guardrail configured for {framework} compliance',
        'blockedInputMessaging': 'This request cannot be processed due to compliance requirements.',
        'blockedOutputsMessaging': 'This response has been blocked due to compliance requirements.'
    }

    # Framework-specific PII handling
    if framework in ['HIPAA', 'GDPR']:
        config['sensitiveInformationPolicyConfig'] = {
            'piiEntitiesConfig': [
                {'type': 'NAME', 'action': 'BLOCK'},
                {'type': 'EMAIL', 'action': 'BLOCK'},
                {'type': 'PHONE', 'action': 'BLOCK'},
                {'type': 'ADDRESS', 'action': 'BLOCK'},
                {'type': 'SSN', 'action': 'BLOCK'},
                {'type': 'CREDIT_DEBIT_CARD_NUMBER', 'action': 'BLOCK'}
            ]
        }

        # HIPAA-specific: Block all PHI-related terms
        if framework = 'HIPAA':
            config['sensitiveInformationPolicyConfig']['piiEntitiesConfig'].extend([
                {'type': 'AWS_ACCESS_KEY', 'action': 'BLOCK'},
                {'type': 'IP_ADDRESS', 'action': 'ANONYMIZE'}
            ])
            config['sensitiveInformationPolicyConfig']['regexesConfig'] = [
                {
                    'name': 'MedicalRecordNumber',
                    'pattern': r'MRN[:\s]?\d{6,10}',
                    'action': 'BLOCK',
                    'description': 'Block medical record numbers'
                }
            ]

    # PCI DSS: Block payment card data
    if framework = 'PCI_DSS':
        config['sensitiveInformationPolicyConfig'] = {
            'piiEntitiesConfig': [
                {'type': 'CREDIT_DEBIT_CARD_NUMBER', 'action': 'BLOCK'},
                {'type': 'CREDIT_DEBIT_CARD_CVV', 'action': 'BLOCK'},
                {'type': 'CREDIT_DEBIT_CARD_EXPIRY', 'action': 'BLOCK'},
                {'type': 'PIN', 'action': 'BLOCK'}
            ]
        }

    # Content filtering for all frameworks
    config['contentPolicyConfig'] = {
        'filtersConfig': [
            {'type': 'SEXUAL', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
            {'type': 'VIOLENCE', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
            {'type': 'HATE', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
            {'type': 'INSULTS', 'inputStrength': 'MEDIUM', 'outputStrength': 'MEDIUM'},
            {'type': 'MISCONDUCT', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
            {'type': 'PROMPT_ATTACK', 'inputStrength': 'HIGH', 'outputStrength': 'NONE'}
        ]
    }

    response = bedrock.create_guardrail(**config)
    print(f"Compliant guardrail created: {response['guardrailId']}")
    return response['guardrailId']


def invoke_with_compliance_logging(
    model_id,
    prompt,
    guardrail_id,
    compliance_metadata
):
    """
    Invoke model with compliance audit logging.
    """
    import hashlib
    from datetime import datetime

    # Create audit record
    audit_record = {
        'timestamp': str(datetime.utcnow()),
        'model_id': model_id,
        'guardrail_id': guardrail_id,
        'prompt_hash': hashlib.sha256(prompt.encode()).hexdigest(),
        'compliance_framework': compliance_metadata.get('framework'),
        'user_id': compliance_metadata.get('user_id'),
        'session_id': compliance_metadata.get('session_id'),
        'purpose': compliance_metadata.get('purpose')
    }

    # Invoke with guardrail
    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        guardrailIdentifier=guardrail_id,
        guardrailVersion='DRAFT',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 1000,
            'messages': [{'role': 'user', 'content': prompt}]
        })
    )

    result = json.loads(response['body'].read())

    # Update audit record with response metadata
    audit_record['response_status'] = 'success'
    audit_record['guardrail_action'] = response.get('ResponseMetadata', {}).get('HTTPHeaders', {}).get('x-amzn-guardrail-action', 'none')
    audit_record['input_tokens'] = result.get('usage', {}).get('input_tokens', 0)
    audit_record['output_tokens'] = result.get('usage', {}).get('output_tokens', 0)

    # Log audit record (send to CloudWatch, S3, or audit system)
    log_compliance_audit(audit_record)

    return result, audit_record


def log_compliance_audit(record):
    """
    Log compliance audit record to appropriate destination.
    """
    cloudwatch_logs = boto3.client('logs')

    cloudwatch_logs.put_log_events(
        logGroupName='/genai/compliance-audit',
        logStreamName=f"audit-{datetime.utcnow().strftime('%Y-%m-%d')}",
        logEvents=[{
            'timestamp': int(datetime.utcnow().timestamp() * 1000),
            'message': json.dumps(record)
        }]
    )


# Example: Create HIPAA-compliant guardrail
guardrail_id = create_compliant_guardrail('HIPAA', 'healthcare-genai-guardrail')

# Invoke with compliance logging
result, audit = invoke_with_compliance_logging(
    model_id='anthropic.claude-3-sonnet-20240229-v1:0',
    prompt='Summarize the patient discharge instructions.',
    guardrail_id=guardrail_id,
    compliance_metadata={
        'framework': 'HIPAA',
        'user_id': 'doctor-123',
        'session_id': 'session-abc',
        'purpose': 'clinical-documentation'
    }
)