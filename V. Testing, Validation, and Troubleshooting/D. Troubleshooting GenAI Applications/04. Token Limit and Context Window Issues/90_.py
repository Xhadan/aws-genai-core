import boto3
import json
from typing import Dict, Any

bedrock_runtime = boto3.client('bedrock-runtime')


class ContextOverflowHandler:
    """
    Handle context overflow with various strategies.
    """

    def __init__(self, model_id: str):
        self.model_id = model_id
        self.token_manager = TokenManager(model_id)
        self.truncator = ContextTruncator(self.token_manager)

    def invoke_with_overflow_handling(
        self,
        prompt: str,
        max_tokens: int,
        system_prompt: str = None,
        strategy: str = 'truncate'
    ) -> Dict[str, Any]:
        """
        Invoke model with automatic overflow handling.

        Strategies:
        - 'truncate': Truncate input to fit
        - 'summarize': Summarize long content first
        - 'chunk': Process in chunks and combine
        - 'error': Raise error if overflow detected
        """
        # Validate request
        validation = self.token_manager.validate_request(
            prompt, max_tokens, system_prompt
        )

        if validation['valid']:
            return self._invoke_model(prompt, max_tokens, system_prompt)

        # Handle overflow based on strategy
        if strategy = 'error':
            raise ValueError(
                f"Context overflow: {validation['issues'][0]['message']}"
            )
        elif strategy = 'truncate':
            return self._handle_truncate(prompt, max_tokens, system_prompt, validation)
        elif strategy = 'summarize':
            return self._handle_summarize(prompt, max_tokens, system_prompt)
        elif strategy = 'chunk':
            return self._handle_chunk(prompt, max_tokens, system_prompt)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _invoke_model(
        self,
        prompt: str,
        max_tokens: int,
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock model.
        """
        body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': max_tokens,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        }

        if system_prompt:
            body['system'] = system_prompt

        response = bedrock_runtime.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )

        result = json.loads(response['body'].read())

        return {
            'content': result['content'][0]['text'],
            'usage': result.get('usage', {}),
            'stop_reason': result.get('stop_reason'),
            'truncated': False
        }

    def _handle_truncate(
        self,
        prompt: str,
        max_tokens: int,
        system_prompt: str,
        validation: Dict
    ) -> Dict[str, Any]:
        """
        Handle overflow by truncating input.
        """
        excess = validation['issues'][0].get('excess', 0)

        # Calculate new target for prompt
        current_prompt_tokens = validation['token_usage']['prompt_tokens']
        target_tokens = current_prompt_tokens - excess - 100  # Buffer

        truncated_prompt, actual_tokens = self.truncator.truncate_to_fit(
            prompt,
            target_tokens,
            strategy='middle'
        )

        result = self._invoke_model(truncated_prompt, max_tokens, system_prompt)
        result['truncated'] = True
        result['original_tokens'] = current_prompt_tokens
        result['truncated_tokens'] = actual_tokens

        return result

    def _handle_summarize(
        self,
        prompt: str,
        max_tokens: int,
        system_prompt: str
    ) -> Dict[str, Any]:
        """
        Handle overflow by summarizing content first.
        """
        # Use a smaller portion for summarization
        summary_max = 1000

        summary_prompt = f"""Summarize the following content concisely while
preserving key information:

{prompt[:50000]}"""  # Take first portion for summarization

        summary_response = self._invoke_model(
            summary_prompt,
            summary_max,
            "You are a summarization assistant. Be concise but preserve important details."
        )

        # Now use the summary
        summarized_prompt = f"""Based on the following summary of the full content:

{summary_response['content']}

{prompt[-5000:]}"""  # Add recent context

        result = self._invoke_model(summarized_prompt, max_tokens, system_prompt)
        result['summarized'] = True

        return result

    def _handle_chunk(
        self,
        prompt: str,
        max_tokens: int,
        system_prompt: str
    ) -> Dict[str, Any]:
        """
        Handle overflow by processing in chunks.
        """
        # Calculate safe chunk size
        context_window = self.token_manager.config['context_window']
        chunk_tokens = context_window // 2  # Use half for input

        chunks = self.truncator.chunk_text(prompt, chunk_tokens)

        chunk_results = []
        for i, chunk in enumerate(chunks):
            chunk_prompt = f"""Process chunk {i + 1} of {len(chunks)}:

{chunk['text']}

Provide key information from this chunk."""

            try:
                result = self._invoke_model(chunk_prompt, max_tokens // len(chunks), system_prompt)
                chunk_results.append(result['content'])
            except Exception as e:
                chunk_results.append(f"[Error processing chunk {i + 1}: {e}]")

        # Combine results
        combined_prompt = f"""Combine and synthesize the following chunk analyses:

{chr(10).join(f'Chunk {i + 1}: {r}' for i, r in enumerate(chunk_results))}

Provide a coherent final response."""

        final_result = self._invoke_model(combined_prompt, max_tokens, system_prompt)
        final_result['chunked'] = True
        final_result['num_chunks'] = len(chunks)

        return final_result


def diagnose_token_error(error: Exception) -> Dict[str, Any]:
    """
    Diagnose token-related errors and provide remediation.
    """
    error_str = str(error)
    diagnosis = {
        'error_type': 'unknown',
        'message': error_str,
        'remediation': []
    }

    if 'ValidationException' in error_str:
        if 'too many tokens' in error_str.lower() or 'context length' in error_str.lower():
            diagnosis['error_type'] = 'context_overflow'
            diagnosis['remediation'] = [
                'Reduce input prompt length',
                'Use summarization for long documents',
                'Implement chunking strategy',
                'Switch to model with larger context window'
            ]
        elif 'max_tokens' in error_str.lower():
            diagnosis['error_type'] = 'invalid_max_tokens'
            diagnosis['remediation'] = [
                'Reduce max_tokens parameter',
                'Check model-specific max_tokens limits',
                'Ensure max_tokens fits within remaining context'
            ]

    elif 'output truncated' in error_str.lower():
        diagnosis['error_type'] = 'output_truncation'
        diagnosis['remediation'] = [
            'Increase max_tokens parameter',
            'Implement continuation requests',
            'Ask for more concise responses'
        ]

    return diagnosis