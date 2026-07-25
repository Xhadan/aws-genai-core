import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime')

class PromptCacheManager:
    """
    Manage Bedrock prompt caching for system prompts and few-shot examples.
    """

    def __init__(self, model_id: str):
        self.model_id = model_id
        self.bedrock = boto3.client('bedrock-runtime')

    def invoke_with_prompt_cache(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: list = None,
        max_tokens: int = 500
    ) -> dict:
        """
        Invoke model with prompt caching for system prompt.

        For Claude models on Bedrock, system prompts can be cached
        when using the Messages API format.
        """
        messages = []

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add current user message
        messages.append({
            'role': 'user',
            'content': [{'text': user_message}]
        })

        # Build request with system prompt
        # Bedrock automatically caches long system prompts (1024+ tokens)
        response = self.bedrock.converse(
            modelId=self.model_id,
            system=[{'text': system_prompt}],
            messages=messages,
            inferenceConfig={'maxTokens': max_tokens}
        )

        # Extract caching metrics from response
        usage = response.get('usage', {})

        return {
            'response': response['output']['message']['content'][0]['text'],
            'input_tokens': usage.get('inputTokens', 0),
            'output_tokens': usage.get('outputTokens', 0),
            'cache_creation_tokens': usage.get('cacheCreationInputTokens', 0),
            'cache_read_tokens': usage.get('cacheReadInputTokens', 0)
        }


class FewShotCacheOptimizer:
    """Optimize few-shot examples for caching"""

    def __init__(self, model_id: str):
        self.model_id = model_id
        self.bedrock = boto3.client('bedrock-runtime')

    def create_cacheable_few_shot_prompt(
        self,
        examples: list,
        task_instruction: str
    ) -> str:
        """
        Create a cacheable few-shot prompt structure.
        Places examples in system prompt for caching.
        """
        # Format examples for caching
        examples_text = "\n\n".join([
            f"Example {i+1}:\nInput: {ex['input']}\nOutput: {ex['output']}"
            for i, ex in enumerate(examples)
        ])

        # Create cacheable system prompt (1024+ tokens for caching)
        system_prompt = f"""{task_instruction}

Here are examples of the expected input/output format:

{examples_text}

Follow the same format for new inputs."""

        return system_prompt

    def invoke_with_cached_examples(
        self,
        system_prompt: str,
        input_text: str,
        max_tokens: int = 200
    ) -> dict:
        """
        Invoke model with cached few-shot examples.
        System prompt containing examples is cached.
        """
        response = self.bedrock.converse(
            modelId=self.model_id,
            system=[{'text': system_prompt}],
            messages=[{
                'role': 'user',
                'content': [{'text': f"Input: {input_text}\nOutput:"}]
            }],
            inferenceConfig={'maxTokens': max_tokens}
        )

        usage = response.get('usage', {})

        return {
            'response': response['output']['message']['content'][0]['text'],
            'input_tokens': usage.get('inputTokens', 0),
            'cache_read_tokens': usage.get('cacheReadInputTokens', 0),
            'cache_write_tokens': usage.get('cacheCreationInputTokens', 0)
        }


# Example: Multi-turn conversation with cached system prompt
cache_manager = PromptCacheManager(
    model_id='anthropic.claude-3-sonnet-20240229-v1:0'
)

# Long system prompt (will be cached)
system_prompt = """You are an expert customer support agent for TechCorp Inc.

Company Information:
- Founded: 2010
- Headquarters: San Francisco, CA
- Products: Enterprise software solutions
- Support hours: 24/7

Product Knowledge:
- TechCorp Suite: All-in-one enterprise management
- TechCorp Analytics: Business intelligence platform
- TechCorp Connect: Communication and collaboration tools

Support Guidelines:
1. Always greet customers professionally
2. Verify customer identity before discussing account details
3. Escalate billing issues to the billing department
4. Log all interactions in the ticketing system
5. Follow up within 24 hours on unresolved issues

Common Issues and Resolutions:
- Login problems: Reset password via self-service portal
- Performance issues: Check system status page first
- Feature requests: Log in product feedback system
- Billing questions: Transfer to billing department

Remember to maintain a helpful, professional tone throughout the conversation."""

# First request - system prompt cached
result1 = cache_manager.invoke_with_prompt_cache(
    system_prompt=system_prompt,
    user_message="Hi, I'm having trouble logging into my account."
)
print(f"First request:")
print(f"  Input tokens: {result1['input_tokens']}")
print(f"  Cache write tokens: {result1['cache_creation_tokens']}")

# Second request - system prompt read from cache
result2 = cache_manager.invoke_with_prompt_cache(
    system_prompt=system_prompt,
    user_message="What are your support hours?",
    conversation_history=[
        {'role': 'user', 'content': [{'text': "Hi, I'm having trouble logging into my account."}]},
        {'role': 'assistant', 'content': [{'text': result1['response']}]}
    ]
)
print(f"\nSecond request:")
print(f"  Input tokens: {result2['input_tokens']}")
print(f"  Cache read tokens: {result2['cache_read_tokens']}")