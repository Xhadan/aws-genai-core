import boto3

comprehend = boto3.client('comprehend')
bedrock_runtime = boto3.client('bedrock-runtime')

class ComprehensivePIIProtection:
    """
    Multi-layer PII protection combining Comprehend and Guardrails.
    """

    def __init__(self, guardrail_id, guardrail_version, confidence_threshold=0.9):
        self.guardrail_id = guardrail_id
        self.guardrail_version = guardrail_version
        self.confidence_threshold = confidence_threshold

    def analyze_with_comprehend(self, text):
        """
        Get detailed PII analysis from Comprehend.
        """
        response = comprehend.detect_pii_entities(
            Text=text,
            LanguageCode='en'
        )

        high_confidence_pii = []
        all_pii = []

        for entity in response['Entities']:
            pii_info = {
                'type': entity['Type'],
                'score': entity['Score'],
                'text': text[entity['BeginOffset']:entity['EndOffset']],
                'position': (entity['BeginOffset'], entity['EndOffset'])
            }
            all_pii.append(pii_info)

            if entity['Score'] >= self.confidence_threshold:
                high_confidence_pii.append(pii_info)

        return {
            'all_pii': all_pii,
            'high_confidence_pii': high_confidence_pii,
            'has_sensitive_pii': self._has_sensitive_types(high_confidence_pii)
        }

    def _has_sensitive_types(self, pii_list):
        """Check for highly sensitive PII types."""
        sensitive_types = {
            'SSN', 'CREDIT_DEBIT_NUMBER', 'BANK_ACCOUNT_NUMBER',
            'PASSPORT_NUMBER', 'DRIVER_ID', 'CREDIT_DEBIT_CVV'
        }
        return any(p['type'] in sensitive_types for p in pii_list)

    def apply_guardrail(self, text, source='INPUT'):
        """Apply Bedrock Guardrails for protection."""
        response = bedrock_runtime.apply_guardrail(
            guardrailIdentifier=self.guardrail_id,
            guardrailVersion=self.guardrail_version,
            source=source,
            content=[{'text': {'text': text}}]
        )

        return {
            'action': response['action'],
            'safe_text': response['outputs'][0]['text'] if response.get('outputs') else None,
            'blocked': response['action'] = 'GUARDRAIL_INTERVENED' and not response.get('outputs')
        }

    def process_with_protection(self, user_input):
        """
        Full PII protection pipeline.
        """
        result = {
            'original': user_input,
            'comprehend_analysis': None,
            'guardrail_result': None,
            'safe_text': None,
            'blocked': False,
            'warnings': []
        }

        # Step 1: Comprehend analysis for detailed insights
        result['comprehend_analysis'] = self.analyze_with_comprehend(user_input)

        # Add warning for sensitive PII even if guardrails handle it
        if result['comprehend_analysis']['has_sensitive_pii']:
            result['warnings'].append('Highly sensitive PII detected (SSN, card numbers, etc.)')

        # Step 2: Apply Guardrails for protection
        result['guardrail_result'] = self.apply_guardrail(user_input, 'INPUT')

        if result['guardrail_result']['blocked']:
            result['blocked'] = True
            result['warnings'].append('Content blocked by guardrails')
        elif result['guardrail_result']['safe_text']:
            result['safe_text'] = result['guardrail_result']['safe_text']
        else:
            result['safe_text'] = user_input

        return result

# Usage
protector = ComprehensivePIIProtection(
    guardrail_id='your-guardrail-id',
    guardrail_version='1',
    confidence_threshold=0.85
)

user_message = "Hi, my name is Jane Doe, email jane@company.com, SSN 987-65-4321"
result = protector.process_with_protection(user_message)

print(f"Blocked: {result['blocked']}")
print(f"Warnings: {result['warnings']}")
print(f"PII found: {len(result['comprehend_analysis']['all_pii'])} entities")
print(f"Safe text: {result['safe_text']}")