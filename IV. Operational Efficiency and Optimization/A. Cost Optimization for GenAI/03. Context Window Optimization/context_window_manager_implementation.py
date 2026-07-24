import boto3
import json
from typing import List, Dict
import tiktoken

bedrock_runtime = boto3.client('bedrock-runtime')

class ContextWindowOptimizer:
    """Optimizes context window usage for cost and quality"""

    def __init__(self, model_id, max_context_tokens0000):
        self.model_id = model_id
        self.max_context_tokens = max_context_tokens
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoder.encode(text))

    def estimate_output_tokens(self, task_type: str) -> int:
        """Estimate output tokens based on task"""
        estimates = {
            'classification': 50,
            'summary': 500,
            'question_answer': 300,
            'generation': 1000,
            'extraction': 200
        }
        return estimates.get(task_type, 500)

    def calculate_available_input_tokens(self, task_type: str) -> int:
        """Calculate available input tokens after reserving output"""
        output_estimate = self.estimate_output_tokens(task_type)
        return self.max_context_tokens - output_estimate

    def optimize_context(
        self,
        system_prompt: str,
        conversation_history: List[Dict],
        retrieved_context: List[str],
        user_query: str,
        task_type: str = 'question_answer'
    ) -> Dict:
        """
        Optimize context to fit within window while maximizing relevance.
        Returns optimized context and metadata.
        """
        available_tokens = self.calculate_available_input_tokens(task_type)

        # Reserve tokens for fixed components
        system_tokens = self.count_tokens(system_prompt)
        query_tokens = self.count_tokens(user_query)
        reserved_tokens = system_tokens + query_tokens + 100  # buffer

        remaining_tokens = available_tokens - reserved_tokens

        # Allocate tokens: 60% context, 40% history (adjustable)
        context_budget = int(remaining_tokens * 0.6)
        history_budget = int(remaining_tokens * 0.4)

        # Optimize retrieved context (most relevant first)
        optimized_context = self._fit_to_budget(
            retrieved_context,
            context_budget
        )

        # Optimize conversation history (most recent first)
        history_texts = [
            f"{msg['role']}: {msg['content']}"
            for msg in conversation_history
        ]
        optimized_history = self._fit_to_budget(
            list(reversed(history_texts)),
            history_budget
        )
        optimized_history = list(reversed(optimized_history))

        total_tokens = (
            system_tokens +
            sum(self.count_tokens(c) for c in optimized_context) +
            sum(self.count_tokens(h) for h in optimized_history) +
            query_tokens
        )

        return {
            'system_prompt': system_prompt,
            'context': optimized_context,
            'history': optimized_history,
            'query': user_query,
            'total_input_tokens': total_tokens,
            'context_items_included': len(optimized_context),
            'context_items_excluded': len(retrieved_context) - len(optimized_context),
            'history_messages_included': len(optimized_history),
            'history_messages_excluded': len(conversation_history) - len(optimized_history)
        }

    def _fit_to_budget(self, items: List[str], budget: int) -> List[str]:
        """Include items until budget exhausted"""
        result = []
        used_tokens = 0

        for item in items:
            item_tokens = self.count_tokens(item)
            if used_tokens + item_tokens <= budget:
                result.append(item)
                used_tokens += item_tokens
            else:
                break

        return result


class ConversationSummarizer:
    """Summarizes conversation history to reduce context size"""

    def __init__(self, model_id='anthropic.claude-3-haiku-20240307-v1:0'):
        self.model_id = model_id
        self.bedrock = boto3.client('bedrock-runtime')

    def summarize_history(
        self,
        messages: List[Dict],
        max_summary_tokens: int = 300
    ) -> str:
        """Create concise summary of conversation history"""

        history_text = "\n".join([
            f"{m['role']}: {m['content']}"
            for m in messages
        ])

        prompt = f"""Summarize this conversation in a single paragraph.
Include: key topics discussed, decisions made, and pending questions.
Keep under 150 words.

Conversation:
{history_text}

Summary:"""

        response = self.bedrock.converse(
            modelId=self.model_id,
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': max_summary_tokens}
        )

        return response['output']['message']['content'][0]['text']

    def create_progressive_context(
        self,
        messages: List[Dict],
        recent_count: int = 5,
        summary_threshold: int = 10
    ) -> List[Dict]:
        """
        Create progressive context with summary + recent messages.
        Summarizes older messages while keeping recent ones intact.
        """
        if len(messages) <= summary_threshold:
            return messages

        # Split messages
        old_messages = messages[:-recent_count]
        recent_messages = messages[-recent_count:]

        # Summarize old messages
        summary = self.summarize_history(old_messages)

        # Create progressive context
        return [
            {'role': 'system', 'content': f'Previous conversation summary: {summary}'}
        ] + recent_messages


# Example usage
optimizer = ContextWindowOptimizer(
    model_id='anthropic.claude-3-sonnet-20240229-v1:0',
    max_context_tokens0000
)

# Simulate inputs
system_prompt = "You are a helpful assistant for customer support."
conversation_history = [
    {'role': 'user', 'content': 'I need help with my order'},
    {'role': 'assistant', 'content': 'I would be happy to help! What is your order number?'},
    {'role': 'user', 'content': 'Order #12345'},
    # ... more messages
]
retrieved_context = [
    "Order #12345 was placed on 2024-01-15 for $150.00...",
    "Customer account created on 2023-06-01...",
    "Previous support tickets: none...",
]
user_query = "When will my order arrive?"

# Optimize context
result = optimizer.optimize_context(
    system_prompt=system_prompt,
    conversation_history=conversation_history,
    retrieved_context=retrieved_context,
    user_query=user_query,
    task_type='question_answer'
)

print(f"Total input tokens: {result['total_input_tokens']}")
print(f"Context items included: {result['context_items_included']}")
print(f"History messages included: {result['history_messages_included']}")