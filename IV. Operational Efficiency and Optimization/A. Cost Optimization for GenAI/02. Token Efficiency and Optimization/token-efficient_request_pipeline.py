import boto3
import json
import tiktoken
from functools import lru_cache

bedrock_runtime = boto3.client('bedrock-runtime')

class TokenEfficientClient:
    """Client optimized for token efficiency"""

    def __init__(self, model_id):
        self.model_id = model_id
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text):
        """Estimate token count"""
        return len(self.encoder.encode(text))

    def optimize_prompt(self, prompt):
        """Apply prompt optimization techniques"""
        optimizations = [
            # Remove extra whitespace
            (' '.join(prompt.split()), 'whitespace'),
            # Remove filler phrases
            (prompt.replace('Please ', '').replace('Could you ', ''), 'filler'),
        ]

        optimized = prompt
        for text, _ in optimizations:
            if self.count_tokens(text) < self.count_tokens(optimized):
                optimized = text

        return optimized

    def create_efficient_system_prompt(self, role, constraints):
        """Create minimal effective system prompt"""
        return f"Role: {role}\nConstraints: {', '.join(constraints)}"

    def invoke_with_limits(
        self,
        user_message,
        system_prompt=None,
        max_output_tokens 0,
        response_format='json'
    ):
        """Invoke with token efficiency controls"""

        messages = []

        if system_prompt:
            messages.append({
                'role': 'user',
                'content': [{'text': f"[System]: {system_prompt}\n\n{user_message}"}]
            })
        else:
            messages.append({
                'role': 'user',
                'content': [{'text': user_message}]
            })

        # Add format instruction if JSON requested
        if response_format = 'json':
            messages[0]['content'][0]['text'] += '\nRespond in JSON only.'

        # Track input tokens
        input_text = messages[0]['content'][0]['text']
        estimated_input = self.count_tokens(input_text)

        response = bedrock_runtime.converse(
            modelId=self.model_id,
            messages=messages,
            inferenceConfig={
                'maxTokens': max_output_tokens,
                'temperature': 0,  # Deterministic for caching
                'stopSequences': ['```', '\n\n\n']  # Early stopping
            }
        )

        usage = response.get('usage', {})

        return {
            'content': response['output']['message']['content'][0]['text'],
            'input_tokens': usage.get('inputTokens', estimated_input),
            'output_tokens': usage.get('outputTokens', 0),
            'total_tokens': usage.get('totalTokens', 0)
        }


class ConversationSummarizer:
    """Summarize conversation history to reduce tokens"""

    def __init__(self, client):
        self.client = client

    def summarize_for_context(self, messages, max_summary_tokens 0):
        """Create efficient summary of conversation history"""
        if len(messages) <= 4:
            return messages  # Don't summarize short conversations

        # Format messages for summarization
        history_text = "\n".join([
            f"{m['role']}: {m['content'][:200]}"
            for m in messages[:-4]  # Summarize all but last 4
        ])

        summary_prompt = f"""Summarize this conversation in under 100 words,
preserving key facts and decisions:

{history_text}"""

        summary_result = self.client.invoke_with_limits(
            user_message=summary_prompt,
            max_output_tokens=max_summary_tokens,
            response_format='text'
        )

        # Return summary + recent messages
        return [
            {'role': 'system', 'content': f"Prior context: {summary_result['content']}"}
        ] + messages[-4:]


# Example usage
client = TokenEfficientClient('anthropic.claude-3-haiku-20240307-v1:0')

# Optimize a verbose prompt
verbose_prompt = """
Please analyze the following customer review and provide
a detailed sentiment analysis. I would like you to determine
if the sentiment is positive, negative, or neutral, and also
provide a confidence score.
"""

optimized = client.optimize_prompt(verbose_prompt)
print(f"Original: {client.count_tokens(verbose_prompt)} tokens")
print(f"Optimized: {client.count_tokens(optimized)} tokens")

# Efficient invocation
result = client.invoke_with_limits(
    user_message="Review: 'Great product, highly recommend!'\nAnalyze sentiment.",
    max_output_tokensP,
    response_format='json'
)

print(f"Response: {result['content']}")
print(f"Input tokens: {result['input_tokens']}")
print(f"Output tokens: {result['output_tokens']}")