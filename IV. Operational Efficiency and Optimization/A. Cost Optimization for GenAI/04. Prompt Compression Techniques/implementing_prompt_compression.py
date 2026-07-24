import boto3
import re
from typing import List, Dict, Tuple
import tiktoken

class PromptCompressor:
    """Implement various prompt compression techniques"""

    def __init__(self):
        self.encoder = tiktoken.get_encoding("cl100k_base")
        # Common filler words to remove
        self.filler_words = {
            'please', 'kindly', 'could you', 'would you',
            'i would like you to', 'i need you to',
            'it would be great if', 'if possible',
            'carefully', 'thoroughly', 'detailed'
        }
        # Verbose to concise mappings
        self.phrase_mappings = {
            'in order to': 'to',
            'due to the fact that': 'because',
            'in the event that': 'if',
            'at this point in time': 'now',
            'for the purpose of': 'to',
            'with regard to': 'about',
            'in addition to': 'also',
            'as a result of': 'from',
            'on the basis of': 'based on',
            'in the case of': 'for'
        }

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoder.encode(text))

    def lexical_compress(self, prompt: str) -> Tuple[str, Dict]:
        """
        Apply lexical compression techniques.
        Returns compressed prompt and statistics.
        """
        original_tokens = self.count_tokens(prompt)
        compressed = prompt.lower()

        # Remove filler phrases
        for filler in self.filler_words:
            compressed = re.sub(
                rf'\b{re.escape(filler)}\b',
                '',
                compressed,
                flags=re.IGNORECASE
            )

        # Apply phrase mappings
        for verbose, concise in self.phrase_mappings.items():
            compressed = compressed.replace(verbose, concise)

        # Clean up whitespace
        compressed = ' '.join(compressed.split())

        final_tokens = self.count_tokens(compressed)

        return compressed, {
            'original_tokens': original_tokens,
            'compressed_tokens': final_tokens,
            'reduction_percent': (1 - final_tokens/original_tokens) * 100
        }

    def compress_few_shot_examples(
        self,
        examples: List[Dict[str, str]],
        max_example_tokens: int = 50
    ) -> str:
        """
        Compress few-shot examples to minimal format.
        Input: [{'input': '...', 'output': '...', 'explanation': '...'}]
        """
        compressed_examples = []

        for ex in examples:
            # Extract just input/output, skip explanations
            input_text = ex.get('input', '')[:100]  # Truncate long inputs
            output_text = ex.get('output', '')

            # Format as minimal pair
            compressed_examples.append(f'"{input_text}" -> {output_text}')

        return "Examples:\n" + "\n".join(compressed_examples)

    def semantic_compress(self, text: str, target_ratio: float = 0.5) -> str:
        """
        Apply semantic compression using importance scoring.
        This is a simplified version - production would use ML models.
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 2:
            return text

        # Score sentences by information density (simplified)
        scored = []
        for sent in sentences:
            # Higher score = more information dense
            score = (
                len(set(sent.lower().split())) /  # Unique word ratio
                max(len(sent.split()), 1) *
                (1 if any(c.isupper() for c in sent[1:]) else 0.8) *  # Named entities
                (1.2 if any(c.isdigit() for c in sent) else 1)  # Numbers
            )
            scored.append((sent, score))

        # Sort by score and keep top portion
        scored.sort(key=lambda x: x[1], reverse=True)
        keep_count = max(1, int(len(scored) * target_ratio))

        # Reconstruct in original order
        kept_sentences = set(s for s, _ in scored[:keep_count])
        result = '. '.join(s for s in sentences if s in kept_sentences)

        return result + '.' if result else text


class LLMLinguaCompressor:
    """
    Simplified LLMLingua-style compression.
    Production implementation would use actual LLMLingua library.
    """

    def __init__(self, model_id='anthropic.claude-3-haiku-20240307-v1:0'):
        self.bedrock = boto3.client('bedrock-runtime')
        self.model_id = model_id

    def compress_with_llm(
        self,
        prompt: str,
        compression_ratio: float = 0.5
    ) -> str:
        """
        Use LLM to compress prompt while preserving key information.
        This simulates LLMLingua behavior for demonstration.
        """
        target_tokens = int(len(prompt.split()) * compression_ratio)

        compression_prompt = f"""Compress this text to approximately {target_tokens} words.
Preserve all key information, entities, and task instructions.
Remove redundant phrases and filler words.
Output ONLY the compressed text.

Text to compress:
{prompt}

Compressed version:"""

        response = self.bedrock.converse(
            modelId=self.model_id,
            messages=[{'role': 'user', 'content': [{'text': compression_prompt}]}],
            inferenceConfig={'maxTokens': target_tokens * 2, 'temperature': 0}
        )

        return response['output']['message']['content'][0]['text']

    def compress_context_for_rag(
        self,
        query: str,
        contexts: List[str],
        target_total_tokens: int = 1000
    ) -> List[str]:
        """
        Compress RAG contexts to fit token budget while preserving relevance.
        """
        # Calculate per-context budget
        per_context_budget = target_total_tokens // len(contexts)

        compressed_contexts = []
        for ctx in contexts:
            if len(ctx.split()) <= per_context_budget:
                compressed_contexts.append(ctx)
            else:
                compressed = self.compress_with_llm(
                    ctx,
                    compression_ratio=per_context_budget / len(ctx.split())
                )
                compressed_contexts.append(compressed)

        return compressed_contexts


# Example usage
compressor = PromptCompressor()

# Test lexical compression
verbose_prompt = """
I would like you to please carefully analyze the following customer
feedback and provide me with a detailed summary. In order to ensure
quality, could you please identify the main themes and any actionable
insights? It would be great if you could format the response as JSON.
"""

compressed, stats = compressor.lexical_compress(verbose_prompt)
print(f"Original: {stats['original_tokens']} tokens")
print(f"Compressed: {stats['compressed_tokens']} tokens")
print(f"Reduction: {stats['reduction_percent']:.1f}%")
print(f"Result: {compressed}")

# Test few-shot compression
examples = [
    {
        'input': 'The product arrived damaged and customer service was unhelpful',
        'output': 'negative',
        'explanation': 'Customer expresses dissatisfaction with both product and service'
    },
    {
        'input': 'Great quality, fast shipping, would buy again',
        'output': 'positive',
        'explanation': 'Customer is satisfied with multiple aspects of the experience'
    }
]

compressed_examples = compressor.compress_few_shot_examples(examples)
print(f"\nCompressed examples:\n{compressed_examples}")