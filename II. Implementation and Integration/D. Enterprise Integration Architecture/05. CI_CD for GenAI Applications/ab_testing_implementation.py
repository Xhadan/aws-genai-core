import boto3
import json
import random
from datetime import datetime
from typing import Optional

dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime')

class PromptABTesting:
    """A/B testing framework for GenAI prompts."""

    def __init__(self, experiment_table: str = "ab-experiments"):
        self.table = dynamodb.Table(experiment_table)

    def create_experiment(
        self,
        experiment_id: str,
        prompt_a: dict,
        prompt_b: dict,
        traffic_split: float = 0.5,
        metrics: list = None
    ):
        """Create a new A/B experiment."""
        self.table.put_item(Item={
            'experiment_id': experiment_id,
            'status': 'running',
            'prompt_a': prompt_a,
            'prompt_b': prompt_b,
            'traffic_split': traffic_split,
            'metrics': metrics or ['latency', 'user_rating', 'completion_rate'],
            'created_at': datetime.utcnow().isoformat(),
            'results_a': {'invocations': 0, 'total_latency': 0, 'ratings': []},
            'results_b': {'invocations': 0, 'total_latency': 0, 'ratings': []}
        })

    def get_variant(self, experiment_id: str, user_id: str) -> tuple:
        """
        Get variant for user (deterministic based on user_id).
        Returns (variant_name, prompt_config)
        """
        experiment = self.table.get_item(
            Key={'experiment_id': experiment_id}
        ).get('Item')

        if not experiment or experiment['status'] != 'running':
            # Return default (A) if experiment not found or ended
            return 'A', experiment.get('prompt_a') if experiment else None

        # Deterministic assignment based on user_id hash
        user_hash = hash(user_id) % 100
        traffic_split = experiment['traffic_split'] * 100

        if user_hash < traffic_split:
            return 'A', experiment['prompt_a']
        else:
            return 'B', experiment['prompt_b']

    def invoke_with_tracking(
        self,
        experiment_id: str,
        user_id: str,
        inputs: dict
    ) -> dict:
        """Invoke model with A/B tracking."""
        variant, prompt_config = self.get_variant(experiment_id, user_id)

        if not prompt_config:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Format prompt
        prompt = prompt_config['template'].format(**inputs)

        # Invoke model with timing
        start_time = datetime.utcnow()

        response = bedrock_runtime.invoke_model(
            modelId=prompt_config['model_id'],
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": prompt_config.get('max_tokens', 1024),
                "messages": [{"role": "user", "content": prompt}]
            })
        )

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        result = json.loads(response['body'].read())

        # Record metrics
        self._record_invocation(experiment_id, variant, latency_ms)

        return {
            'variant': variant,
            'response': result['content'][0]['text'],
            'latency_ms': latency_ms,
            'experiment_id': experiment_id
        }

    def _record_invocation(self, experiment_id: str, variant: str, latency_ms: float):
        """Record invocation metrics."""
        results_key = f'results_{variant.lower()}'

        self.table.update_item(
            Key={'experiment_id': experiment_id},
            UpdateExpression=f'''
                SET {results_key}.invocations = {results_key}.invocations + :one,
                    {results_key}.total_latency = {results_key}.total_latency + :latency
            ''',
            ExpressionAttributeValues={
                ':one': 1,
                ':latency': int(latency_ms)
            }
        )

    def record_user_feedback(
        self,
        experiment_id: str,
        variant: str,
        rating: int,
        feedback: Optional[str] = None
    ):
        """Record user feedback for a variant."""
        results_key = f'results_{variant.lower()}'

        self.table.update_item(
            Key={'experiment_id': experiment_id},
            UpdateExpression=f'SET {results_key}.ratings = list_append({results_key}.ratings, :rating)',
            ExpressionAttributeValues={
                ':rating': [{'rating': rating, 'feedback': feedback, 'timestamp': datetime.utcnow().isoformat()}]
            }
        )

    def get_experiment_results(self, experiment_id: str) -> dict:
        """Get current experiment results."""
        experiment = self.table.get_item(
            Key={'experiment_id': experiment_id}
        ).get('Item')

        if not experiment:
            return None

        results_a = experiment['results_a']
        results_b = experiment['results_b']

        def calc_stats(results):
            invocations = results['invocations']
            if invocations = 0:
                return {'invocations': 0, 'avg_latency': 0, 'avg_rating': 0}

            ratings = [r['rating'] for r in results.get('ratings', [])]
            return {
                'invocations': invocations,
                'avg_latency': results['total_latency'] / invocations,
                'avg_rating': sum(ratings) / len(ratings) if ratings else 0,
                'rating_count': len(ratings)
            }

        return {
            'experiment_id': experiment_id,
            'status': experiment['status'],
            'variant_a': calc_stats(results_a),
            'variant_b': calc_stats(results_b)
        }

# Usage example
ab_testing = PromptABTesting()

# Create experiment
ab_testing.create_experiment(
    experiment_id='summarize-v2-test',
    prompt_a={
        'template': 'Summarize in 3 bullet points:\n{text}',
        'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
        'max_tokens': 500
    },
    prompt_b={
        'template': 'You are an expert analyst. Create a concise 3-point summary:\n{text}',
        'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
        'max_tokens': 500
    },
    traffic_split=0.5
)