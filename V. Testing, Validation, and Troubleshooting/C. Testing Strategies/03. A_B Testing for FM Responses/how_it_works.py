import boto3
import hashlib
import json
from datetime import datetime
from typing import Dict, Optional
import random

bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

class GenAIExperiment:
    """A/B testing framework for GenAI applications."""

    def __init__(
        self,
        experiment_id: str,
        variants: Dict[str, Dict],
        traffic_split: Dict[str, float]
    ):
        """
        Initialize experiment.

        variants: {
            'A': {'model_id': '...', 'system_prompt': '...', 'temperature': 0.7},
            'B': {'model_id': '...', 'system_prompt': '...', 'temperature': 0.3}
        }
        traffic_split: {'A': 0.5, 'B': 0.5}
        """
        self.experiment_id = experiment_id
        self.variants = variants
        self.traffic_split = traffic_split
        self.results_table = dynamodb.Table('ExperimentResults')

    def get_variant(self, user_id: str) -> str:
        """Deterministically assign user to variant."""
        hash_input = f"{self.experiment_id}:{user_id}"
        hash_val = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        bucket = (hash_val % 100) / 100

        cumulative = 0
        for variant, split in self.traffic_split.items():
            cumulative += split
            if bucket < cumulative:
                return variant

        return list(self.variants.keys())[0]

    def invoke_variant(self, variant: str, user_message: str) -> Dict:
        """Invoke model with variant configuration."""
        config = self.variants[variant]

        start_time = datetime.utcnow()

        messages = [{'role': 'user', 'content': [{'text': user_message}]}]

        # Add system prompt if configured
        system = []
        if 'system_prompt' in config:
            system = [{'text': config['system_prompt']}]

        response = bedrock_runtime.converse(
            modelId=config['model_id'],
            messages=messages,
            system=system,
            inferenceConfig={
                'maxTokens': config.get('max_tokens', 1024),
                'temperature': config.get('temperature', 0.7)
            }
        )

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return {
            'response': response['output']['message']['content'][0]['text'],
            'latency_ms': latency_ms,
            'input_tokens': response['usage']['inputTokens'],
            'output_tokens': response['usage']['outputTokens'],
            'variant': variant
        }

    def run_experiment(self, user_id: str, user_message: str) -> Dict:
        """Execute experiment for a user request."""

        variant = self.get_variant(user_id)
        result = self.invoke_variant(variant, user_message)

        # Log experiment result
        self._log_result(user_id, user_message, result)

        return result

    def _log_result(self, user_id: str, message: str, result: Dict):
        """Store experiment result for analysis."""
        self.results_table.put_item(Item={
            'experiment_id': self.experiment_id,
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'variant': result['variant'],
            'latency_ms': int(result['latency_ms']),
            'input_tokens': result['input_tokens'],
            'output_tokens': result['output_tokens'],
            'message_preview': message[:100],
            'response_preview': result['response'][:200]
        })

# Example usage
experiment = GenAIExperiment(
    experiment_id='prompt-v2-test-001',
    variants={
        'A': {
            'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
            'system_prompt': 'You are a helpful assistant.',
            'temperature': 0.7
        },
        'B': {
            'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
            'system_prompt': 'You are an expert AWS solutions architect. Provide detailed, technical responses.',
            'temperature': 0.5
        }
    },
    traffic_split={'A': 0.5, 'B': 0.5}
)

result = experiment.run_experiment('user-123', 'How do I set up S3 replication?')