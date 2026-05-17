import boto3
import json
import numpy as np
from typing import List, Dict

bedrock = boto3.client('bedrock-runtime')

class DynamicFewShotClassifier:
    """Few-shot classifier with dynamic example selection."""

    def __init__(self, examples: List[Dict], categories: List[str]):
        self.examples = examples
        self.categories = categories
        self.embeddings = []
        self._embed_examples()

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Titan Embeddings."""
        response = bedrock.invoke_model(
            modelId='amazon.titan-embed-text-v2:0',
            body=json.dumps({"inputText": text})
        )
        result = json.loads(response['body'].read())
        return result['embedding']

    def _embed_examples(self):
        """Pre-compute embeddings for all examples."""
        for ex in self.examples:
            embedding = self._get_embedding(ex['text'])
            self.embeddings.append(embedding)

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def _select_examples(self, query: str, k: int = 3) -> List[Dict]:
        """Select k most similar examples to the query."""
        query_embedding = self._get_embedding(query)

        similarities = []
        for i, emb in enumerate(self.embeddings):
            sim = self._cosine_similarity(query_embedding, emb)
            similarities.append((sim, i))

        # Sort by similarity descending
        similarities.sort(reverse=True)

        # Return top k examples
        selected = []
        for sim, idx in similarities[:k]:
            selected.append(self.examples[idx])

        return selected

    def classify(self, text: str, num_examples: int = 3) -> str:
        """Classify text using dynamically selected examples."""
        # Select most relevant examples
        selected_examples = self._select_examples(text, k=num_examples)

        # Build prompt with selected examples
        examples_text = ""
        for ex in selected_examples:
            examples_text += f"""Text: "{ex['text']}"
Category: {ex['category']}

"""

        prompt = f"""Classify the text into one of these categories: {', '.join(self.categories)}

Here are some similar examples:

{examples_text}Now classify this text:
Text: "{text}"
Category:"""

        response = bedrock.converse(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 50, "temperature": 0}
        )

        return response['output']['message']['content'][0]['text'].strip()


# Example usage
example_bank = [
    {"text": "My EC2 instance won't start", "category": "Compute"},
    {"text": "S3 bucket access denied error", "category": "Storage"},
    {"text": "RDS connection timeout", "category": "Database"},
    {"text": "Lambda memory exceeded", "category": "Compute"},
    {"text": "DynamoDB throttling errors", "category": "Database"},
    {"text": "EBS volume full", "category": "Storage"},
    {"text": "ECS task keeps restarting", "category": "Compute"},
    {"text": "Aurora failover issues", "category": "Database"},
    {"text": "S3 replication lag", "category": "Storage"},
]

classifier = DynamicFewShotClassifier(
    examples=example_bank,
    categories=["Compute", "Storage", "Database", "Network"]
)

# Classify new text - will use most similar examples
result = classifier.classify("My Fargate container is running out of memory")
print(f"Classification: {result}")  # Should be "Compute"