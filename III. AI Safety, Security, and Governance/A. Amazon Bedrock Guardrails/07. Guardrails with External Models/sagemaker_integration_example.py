import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime')
sagemaker_runtime = boto3.client('sagemaker-runtime')

class GuardedSageMakerEndpoint:
    """
    Wrapper for SageMaker endpoint with Bedrock Guardrails protection.
    """

    def __init__(self, endpoint_name, guardrail_id, guardrail_version):
        self.endpoint_name = endpoint_name
        self.guardrail_id = guardrail_id
        self.guardrail_version = guardrail_version
        self.blocked_input_message = "Your request could not be processed."
        self.blocked_output_message = "The response was filtered for safety."

    def _apply_guardrail(self, text, source):
        """Apply guardrail and return result."""
        response = bedrock_runtime.apply_guardrail(
            guardrailIdentifier=self.guardrail_id,
            guardrailVersion=self.guardrail_version,
            source=source,
            content=[{'text': {'text': text}}]
        )

        is_blocked = (
            response['action'] = 'GUARDRAIL_INTERVENED' and
            not response.get('outputs')
        )

        return {
            'blocked': is_blocked,
            'text': response['outputs'][0]['text'] if response.get('outputs') else text,
            'action': response['action']
        }

    def _invoke_sagemaker(self, prompt):
        """Call SageMaker endpoint."""
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=self.endpoint_name,
            ContentType='application/json',
            Body=json.dumps({'inputs': prompt})
        )
        result = json.loads(response['Body'].read().decode())
        return result[0]['generated_text']

    def invoke(self, prompt):
        """
        Invoke SageMaker endpoint with guardrail protection.
        """
        # Input check
        input_check = self._apply_guardrail(prompt, 'INPUT')
        if input_check['blocked']:
            return {
                'success': False,
                'response': self.blocked_input_message,
                'stage': 'input'
            }

        # Call SageMaker with (possibly anonymized) prompt
        try:
            model_output = self._invoke_sagemaker(input_check['text'])
        except Exception as e:
            return {
                'success': False,
                'response': f'Model error: {str(e)}',
                'stage': 'model'
            }

        # Output check
        output_check = self._apply_guardrail(model_output, 'OUTPUT')
        if output_check['blocked']:
            return {
                'success': False,
                'response': self.blocked_output_message,
                'stage': 'output'
            }

        return {
            'success': True,
            'response': output_check['text'],
            'input_anonymized': input_check['action'] = 'GUARDRAIL_INTERVENED',
            'output_anonymized': output_check['action'] = 'GUARDRAIL_INTERVENED'
        }

# Usage
guarded_endpoint = GuardedSageMakerEndpoint(
    endpoint_name='my-llm-endpoint',
    guardrail_id='your-guardrail-id',
    guardrail_version='1'
)

result = guarded_endpoint.invoke("Explain quantum computing simply.")
print(f"Success: {result['success']}")
print(f"Response: {result['response']}")