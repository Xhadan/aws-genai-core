import boto3
import pytest
from typing import Dict, List
import numpy as np

bedrock_runtime = boto3.client('bedrock-runtime')
bedrock_agent = boto3.client('bedrock-agent-runtime')

class TestRAGPipeline:
    """Integration tests for RAG pipeline."""

    KNOWLEDGE_BASE_ID = "test-kb-12345"
    MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"

    @pytest.fixture(scope="class")
    def test_data(self):
        """Test data with known answers."""
        return [
            {
                "query": "What is the maximum Lambda timeout?",
                "expected_keywords": ["15 minutes", "900 seconds"],
                "expected_topic": "Lambda timeout configuration"
            },
            {
                "query": "How many S3 storage classes are there?",
                "expected_keywords": ["storage class", "Standard", "Glacier"],
                "expected_topic": "S3 storage classes"
            }
        ]

    def test_retrieval_returns_relevant_chunks(self, test_data):
        """Test that retrieval returns relevant documents."""

        for test_case in test_data:
            response = bedrock_agent.retrieve(
                knowledgeBaseId=self.KNOWLEDGE_BASE_ID,
                retrievalQuery={'text': test_case['query']},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {'numberOfResults': 5}
                }
            )

            # Verify chunks were retrieved
            assert len(response['retrievalResults']) > 0

            # Check relevance scores
            top_score = response['retrievalResults'][0]['score']
            assert top_score > 0.5, f"Top chunk score too low: {top_score}"

            # Verify at least one chunk contains expected keywords
            all_content = ' '.join([
                r['content']['text'] for r in response['retrievalResults']
            ])

            keyword_found = any(
                kw.lower() in all_content.lower()
                for kw in test_case['expected_keywords']
            )
            assert keyword_found, f"No expected keywords found for: {test_case['query']}"

    def test_end_to_end_rag_response(self, test_data):
        """Test complete RAG flow returns quality response."""

        for test_case in test_data:
            # Execute RAG query
            response = bedrock_agent.retrieve_and_generate(
                input={'text': test_case['query']},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.KNOWLEDGE_BASE_ID,
                        'modelArn': f'arn:aws:bedrock:us-east-1::foundation-model/{self.MODEL_ID}'
                    }
                }
            )

            generated_text = response['output']['text']

            # Verify response is not empty
            assert len(generated_text) > 50, "Response too short"

            # Check for expected keywords in response
            keyword_found = any(
                kw.lower() in generated_text.lower()
                for kw in test_case['expected_keywords']
            )
            assert keyword_found, f"Response missing expected keywords: {test_case['query']}"

            # Verify citations exist
            citations = response.get('citations', [])
            assert len(citations) > 0, "No citations provided"

    def test_semantic_relevance_of_response(self, test_data):
        """Test that responses are semantically relevant."""

        def get_embedding(text: str) -> List[float]:
            response = bedrock_runtime.invoke_model(
                modelId='amazon.titan-embed-text-v2:0',
                body=json.dumps({'inputText': text})
            )
            return json.loads(response['body'].read())['embedding']

        def cosine_similarity(a, b):
            a, b = np.array(a), np.array(b)
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

        for test_case in test_data:
            # Get RAG response
            response = bedrock_agent.retrieve_and_generate(
                input={'text': test_case['query']},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.KNOWLEDGE_BASE_ID,
                        'modelArn': f'arn:aws:bedrock:us-east-1::foundation-model/{self.MODEL_ID}'
                    }
                }
            )

            generated_text = response['output']['text']

            # Calculate semantic similarity
            query_embedding = get_embedding(test_case['query'])
            response_embedding = get_embedding(generated_text)

            similarity = cosine_similarity(query_embedding, response_embedding)
            assert similarity > 0.5, f"Response not semantically relevant: {similarity}"