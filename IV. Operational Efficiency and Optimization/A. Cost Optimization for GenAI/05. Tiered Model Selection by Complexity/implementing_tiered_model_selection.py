import boto3
import json
from typing import Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

class ModelTier(Enum):
    ECONOMY = "economy"
    BALANCED = "balanced"
    PREMIUM = "premium"

@dataclass
class ModelConfig:
    model_id: str
    tier: ModelTier
    input_cost_per_1k: float
    output_cost_per_1k: float
    max_tokens: int

class TieredModelRouter:
    """Routes requests to appropriate model tier based on task requirements"""

    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime')

        # Model configurations
        self.models = {
            ModelTier.ECONOMY: ModelConfig(
                model_id='anthropic.claude-3-haiku-20240307-v1:0',
                tier=ModelTier.ECONOMY,
                input_cost_per_1k=0.00025,
                output_cost_per_1k=0.00125,
                max_tokens@96
            ),
            ModelTier.BALANCED: ModelConfig(
                model_id='anthropic.claude-3-5-sonnet-20241022-v2:0',
                tier=ModelTier.BALANCED,
                input_cost_per_1k=0.003,
                output_cost_per_1k=0.015,
                max_tokens92
            ),
            ModelTier.PREMIUM: ModelConfig(
                model_id='anthropic.claude-3-opus-20240229-v1:0',
                tier=ModelTier.PREMIUM,
                input_cost_per_1k=0.015,
                output_cost_per_1k=0.075,
                max_tokens@96
            )
        }

        # Task-to-tier mapping
        self.task_routing = {
            'classification': ModelTier.ECONOMY,
            'sentiment': ModelTier.ECONOMY,
            'entity_extraction': ModelTier.ECONOMY,
            'short_qa': ModelTier.ECONOMY,
            'summarization': ModelTier.BALANCED,
            'content_generation': ModelTier.BALANCED,
            'code_generation': ModelTier.BALANCED,
            'translation': ModelTier.BALANCED,
            'complex_reasoning': ModelTier.PREMIUM,
            'creative_writing': ModelTier.PREMIUM,
            'multi_document_analysis': ModelTier.PREMIUM,
            'expert_advice': ModelTier.PREMIUM
        }

    def classify_task(self, prompt: str, task_hint: Optional[str] = None) -> str:
        """Classify task type from prompt or explicit hint"""
        if task_hint and task_hint in self.task_routing:
            return task_hint

        # Simple heuristic classification
        prompt_lower = prompt.lower()

        if any(kw in prompt_lower for kw in ['classify', 'categorize', 'is this']):
            return 'classification'
        elif any(kw in prompt_lower for kw in ['sentiment', 'positive', 'negative']):
            return 'sentiment'
        elif any(kw in prompt_lower for kw in ['extract', 'find all', 'list the']):
            return 'entity_extraction'
        elif any(kw in prompt_lower for kw in ['summarize', 'summary', 'key points']):
            return 'summarization'
        elif any(kw in prompt_lower for kw in ['write', 'generate', 'create']):
            return 'content_generation'
        elif any(kw in prompt_lower for kw in ['code', 'function', 'implement']):
            return 'code_generation'
        elif any(kw in prompt_lower for kw in ['analyze', 'compare', 'evaluate']):
            return 'complex_reasoning'

        return 'content_generation'  # Default

    def select_model_tier(
        self,
        prompt: str,
        task_hint: Optional[str] = None,
        quality_requirement: str = 'standard',
        max_budget: Optional[float] = None
    ) -> ModelTier:
        """
        Select appropriate model tier based on task and constraints.

        Args:
            prompt: User prompt
            task_hint: Explicit task type hint
            quality_requirement: 'economy', 'standard', or 'premium'
            max_budget: Maximum cost for this request
        """
        # Classify task
        task_type = self.classify_task(prompt, task_hint)
        base_tier = self.task_routing.get(task_type, ModelTier.BALANCED)

        # Adjust for quality requirement
        if quality_requirement = 'economy':
            return ModelTier.ECONOMY
        elif quality_requirement = 'premium':
            return ModelTier.PREMIUM

        # Adjust for budget constraint
        if max_budget is not None:
            estimated_tokens = len(prompt.split()) * 1.3 + 500
            for tier in [ModelTier.ECONOMY, ModelTier.BALANCED, ModelTier.PREMIUM]:
                config = self.models[tier]
                estimated_cost = (
                    (estimated_tokens / 1000) * config.input_cost_per_1k +
                    (500 / 1000) * config.output_cost_per_1k
                )
                if estimated_cost <= max_budget and tier.value >= base_tier.value:
                    return tier
            return ModelTier.ECONOMY  # Budget constraint forces economy

        return base_tier

    def invoke(
        self,
        prompt: str,
        task_hint: Optional[str] = None,
        quality_requirement: str = 'standard',
        max_budget: Optional[float] = None,
        max_tokens: int = 500
    ) -> Dict:
        """Invoke model with automatic tier selection"""

        tier = self.select_model_tier(
            prompt, task_hint, quality_requirement, max_budget
        )
        config = self.models[tier]

        response = self.bedrock.converse(
            modelId=config.model_id,
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': min(max_tokens, config.max_tokens)}
        )

        usage = response.get('usage', {})
        input_tokens = usage.get('inputTokens', 0)
        output_tokens = usage.get('outputTokens', 0)

        # Calculate cost
        cost = (
            (input_tokens / 1000) * config.input_cost_per_1k +
            (output_tokens / 1000) * config.output_cost_per_1k
        )

        return {
            'response': response['output']['message']['content'][0]['text'],
            'model_tier': tier.value,
            'model_id': config.model_id,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost': cost
        }


# Example usage
router = TieredModelRouter()

# Simple classification - routes to economy
result1 = router.invoke(
    prompt="Classify this review as positive or negative: 'Great product!'",
    task_hint='classification'
)
print(f"Classification: {result1['model_tier']} (${result1['cost']:.6f})")

# Content generation - routes to balanced
result2 = router.invoke(
    prompt="Write a product description for a wireless bluetooth speaker.",
    task_hint='content_generation'
)
print(f"Generation: {result2['model_tier']} (${result2['cost']:.6f})")

# Complex analysis - routes to premium
result3 = router.invoke(
    prompt="Analyze the competitive landscape for electric vehicles, comparing Tesla, BYD, and traditional automakers' strategies.",
    task_hint='complex_reasoning'
)
print(f"Analysis: {result3['model_tier']} (${result3['cost']:.6f})")