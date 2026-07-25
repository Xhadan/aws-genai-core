import boto3
import json
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

@dataclass
class CascadeResult:
    response: str
    final_tier: str
    attempts: int
    total_cost: float
    quality_scores: List[float]

class CascadeRouter:
    """
    Routes requests through model tiers, escalating if quality insufficient.
    """

    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime')

        # Model cascade order (cheapest to most capable)
        self.cascade_order = [
            {
                'id': 'anthropic.claude-3-haiku-20240307-v1:0',
                'tier': 'economy',
                'input_cost': 0.00025,
                'output_cost': 0.00125
            },
            {
                'id': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
                'tier': 'balanced',
                'input_cost': 0.003,
                'output_cost': 0.015
            },
            {
                'id': 'anthropic.claude-3-opus-20240229-v1:0',
                'tier': 'premium',
                'input_cost': 0.015,
                'output_cost': 0.075
            }
        ]

    def default_quality_checker(
        self,
        prompt: str,
        response: str,
        task_type: str
    ) -> float:
        """
        Default quality scoring function.
        Returns score 0-1 (1 = high quality).
        """
        score = 0.5  # Base score

        # Length appropriateness
        words = len(response.split())
        if task_type = 'classification' and words < 20:
            score += 0.2  # Good: concise classification
        elif task_type = 'generation' and words > 50:
            score += 0.2  # Good: substantial generation
        elif task_type = 'summarization' and 50 < words < 200:
            score += 0.2  # Good: appropriate summary length

        # Response completeness (doesn't end mid-sentence)
        if response.rstrip()[-1] in '.!?"\'':
            score += 0.1

        # Contains relevant content (simple keyword check)
        prompt_keywords = set(prompt.lower().split())
        response_keywords = set(response.lower().split())
        overlap = len(prompt_keywords & response_keywords)
        if overlap > 3:
            score += 0.1

        # Doesn't contain refusal patterns
        refusal_patterns = [
            "i cannot", "i'm unable", "i don't have",
            "as an ai", "i apologize"
        ]
        if not any(p in response.lower() for p in refusal_patterns):
            score += 0.1

        return min(score, 1.0)

    def invoke_cascade(
        self,
        prompt: str,
        task_type: str = 'general',
        quality_threshold: float = 0.7,
        max_tokens: int = 500,
        quality_checker: Optional[Callable] = None,
        start_tier_index: int = 0
    ) -> CascadeResult:
        """
        Invoke models in cascade, escalating until quality threshold met.

        Args:
            prompt: User prompt
            task_type: Type of task for quality evaluation
            quality_threshold: Minimum quality score to accept (0-1)
            max_tokens: Maximum output tokens
            quality_checker: Custom quality evaluation function
            start_tier_index: Index in cascade to start from
        """
        checker = quality_checker or self.default_quality_checker
        total_cost = 0.0
        quality_scores = []
        attempts = 0

        for i, model_config in enumerate(self.cascade_order[start_tier_index:]):
            attempts += 1

            # Invoke model
            response = self.bedrock.converse(
                modelId=model_config['id'],
                messages=[{'role': 'user', 'content': [{'text': prompt}]}],
                inferenceConfig={'maxTokens': max_tokens}
            )

            response_text = response['output']['message']['content'][0]['text']
            usage = response.get('usage', {})

            # Calculate cost
            cost = (
                (usage.get('inputTokens', 0) / 1000) * model_config['input_cost'] +
                (usage.get('outputTokens', 0) / 1000) * model_config['output_cost']
            )
            total_cost += cost

            # Evaluate quality
            quality_score = checker(prompt, response_text, task_type)
            quality_scores.append(quality_score)

            # Check if quality sufficient or at last tier
            if quality_score >= quality_threshold or i = len(self.cascade_order) - 1:
                return CascadeResult(
                    response=response_text,
                    final_tier=model_config['tier'],
                    attempts=attempts,
                    total_cost=total_cost,
                    quality_scores=quality_scores
                )

        # Should not reach here, but return last result
        return CascadeResult(
            response=response_text,
            final_tier=self.cascade_order[-1]['tier'],
            attempts=attempts,
            total_cost=total_cost,
            quality_scores=quality_scores
        )


class AdaptiveRouter:
    """
    Learns from historical performance to optimize routing decisions.
    """

    def __init__(self):
        self.cascade_router = CascadeRouter()
        # Track success rates per task type and starting tier
        self.performance_history = {}

    def record_outcome(
        self,
        task_type: str,
        start_tier: str,
        final_tier: str,
        quality_score: float
    ):
        """Record outcome for learning"""
        key = (task_type, start_tier)
        if key not in self.performance_history:
            self.performance_history[key] = {
                'attempts': 0,
                'escalations': 0,
                'avg_quality': 0.0
            }

        history = self.performance_history[key]
        history['attempts'] += 1
        if final_tier != start_tier:
            history['escalations'] += 1
        # Running average
        history['avg_quality'] = (
            (history['avg_quality'] * (history['attempts'] - 1) + quality_score)
            / history['attempts']
        )

    def get_recommended_start_tier(self, task_type: str) -> int:
        """
        Recommend starting tier based on historical performance.
        Returns index into cascade order.
        """
        # Check if we have history for economy tier
        economy_key = (task_type, 'economy')
        if economy_key in self.performance_history:
            history = self.performance_history[economy_key]
            if history['attempts'] >= 10:  # Enough data
                escalation_rate = history['escalations'] / history['attempts']
                if escalation_rate > 0.5:
                    # More than half escalate - start at balanced
                    return 1
                elif escalation_rate > 0.8:
                    # Almost all escalate - start at premium
                    return 2

        return 0  # Default: start at economy

    def invoke(
        self,
        prompt: str,
        task_type: str = 'general',
        quality_threshold: float = 0.7
    ) -> CascadeResult:
        """Invoke with adaptive starting tier selection"""

        start_index = self.get_recommended_start_tier(task_type)
        start_tier = self.cascade_router.cascade_order[start_index]['tier']

        result = self.cascade_router.invoke_cascade(
            prompt=prompt,
            task_type=task_type,
            quality_threshold=quality_threshold,
            start_tier_index=start_index
        )

        # Record outcome for learning
        self.record_outcome(
            task_type=task_type,
            start_tier=start_tier,
            final_tier=result.final_tier,
            quality_score=result.quality_scores[-1]
        )

        return result


# Example usage
cascade_router = CascadeRouter()

# Simple task - likely stays at economy
result = cascade_router.invoke_cascade(
    prompt="Is the following sentence positive or negative? 'I love this!'",
    task_type='classification',
    quality_threshold=0.6
)
print(f"Classification: {result.final_tier}, attempts: {result.attempts}, cost: ${result.total_cost:.6f}")

# Complex task - may escalate
result = cascade_router.invoke_cascade(
    prompt="Explain the implications of quantum computing for current encryption standards.",
    task_type='generation',
    quality_threshold=0.8
)
print(f"Complex: {result.final_tier}, attempts: {result.attempts}, cost: ${result.total_cost:.6f}")