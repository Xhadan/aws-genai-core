import boto3
import json
import re
from jsonschema import validate, ValidationError

bedrock_runtime = boto3.client('bedrock-runtime')

class GenAIValidator:
    """
    Comprehensive input/output validation for GenAI applications.
    """

    def __init__(self, guardrail_id, guardrail_version, max_input_length00):
        self.guardrail_id = guardrail_id
        self.guardrail_version = guardrail_version
        self.max_input_length = max_input_length

        # PII patterns for output validation
        self.pii_patterns = {
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'email': r'\b[\w.-]+@[\w.-]+\.\w+\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        }

    # INPUT VALIDATION
    def validate_input(self, user_input, session_context=None):
        """
        Validate user input before sending to model.
        """
        errors = []

        # 1. Type check
        if not isinstance(user_input, str):
            errors.append("Input must be a string")
            return {'valid': False, 'errors': errors}

        # 2. Empty check
        if not user_input.strip():
            errors.append("Input cannot be empty")
            return {'valid': False, 'errors': errors}

        # 3. Length check
        if len(user_input) > self.max_input_length:
            errors.append(f"Input exceeds maximum length of {self.max_input_length}")
            return {'valid': False, 'errors': errors}

        # 4. Encoding check
        try:
            user_input.encode('utf-8')
        except UnicodeError:
            errors.append("Input contains invalid characters")
            return {'valid': False, 'errors': errors}

        # 5. Guardrails check
        guardrail_result = self._apply_guardrail(user_input, 'INPUT')
        if guardrail_result['blocked']:
            errors.append("Input blocked by content safety filters")
            return {'valid': False, 'errors': errors}

        return {
            'valid': True,
            'sanitized_input': guardrail_result.get('output', user_input),
            'errors': errors
        }

    # OUTPUT VALIDATION
    def validate_output(self, model_output, expected_schema=None):
        """
        Validate model output before returning to user.
        """
        warnings = []
        errors = []

        # 1. Guardrails output check
        guardrail_result = self._apply_guardrail(model_output, 'OUTPUT')
        if guardrail_result['blocked']:
            return {
                'valid': False,
                'errors': ['Output blocked by content safety filters'],
                'warnings': warnings
            }

        safe_output = guardrail_result.get('output', model_output)

        # 2. PII leakage check (additional layer)
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, safe_output):
                warnings.append(f"Potential {pii_type} detected in output")

        # 3. Schema validation (if structured output expected)
        if expected_schema:
            try:
                output_json = json.loads(safe_output)
                validate(instance=output_json, schema=expected_schema)
            except json.JSONDecodeError:
                errors.append("Output is not valid JSON")
            except ValidationError as e:
                errors.append(f"Output doesn't match schema: {e.message}")

        # 4. Length check
        if len(safe_output) > 50000:  # Arbitrary large response limit
            warnings.append("Unusually long response")

        return {
            'valid': len(errors) = 0,
            'output': safe_output,
            'errors': errors,
            'warnings': warnings
        }

    def _apply_guardrail(self, text, source):
        """
        Apply Guardrails for content validation.
        """
        response = bedrock_runtime.apply_guardrail(
            guardrailIdentifier=self.guardrail_id,
            guardrailVersion=self.guardrail_version,
            source=source,
            content=[{'text': {'text': text}}]
        )

        blocked = (response['action'] = 'GUARDRAIL_INTERVENED' and
                   not response.get('outputs'))

        return {
            'blocked': blocked,
            'output': response['outputs'][0]['text'] if response.get('outputs') else text
        }

    def process_request(self, user_input, expected_output_schema=None):
        """
        Full request processing with validation.
        """
        # Validate input
        input_result = self.validate_input(user_input)
        if not input_result['valid']:
            return {
                'success': False,
                'stage': 'input_validation',
                'errors': input_result['errors']
            }

        # Call model (simplified)
        model_output = self._invoke_model(input_result['sanitized_input'])

        # Validate output
        output_result = self.validate_output(model_output, expected_output_schema)
        if not output_result['valid']:
            return {
                'success': False,
                'stage': 'output_validation',
                'errors': output_result['errors']
            }

        return {
            'success': True,
            'response': output_result['output'],
            'warnings': output_result['warnings']
        }

    def _invoke_model(self, prompt):
        """Invoke model (simplified)."""
        response = bedrock_runtime.converse(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': 1024}
        )
        return response['output']['message']['content'][0]['text']

# Usage
validator = GenAIValidator(
    guardrail_id='your-guardrail-id',
    guardrail_version='1',
    max_input_length@00
)

result = validator.process_request("What is the capital of France?")
print(f"Success: {result['success']}")
if result['success']:
    print(f"Response: {result['response']}")
else:
    print(f"Errors: {result['errors']}")