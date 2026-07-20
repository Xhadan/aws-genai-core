import boto3
import json
from typing import List, Dict

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

def retrieve_and_generate_with_citations(
    knowledge_base_id: str,
    model_arn: str,
    query: str,
    max_results: int = 5
) -> Dict:
    """
    Query Bedrock Knowledge Base and extract citations.
    """
    response = bedrock_agent_runtime.retrieve_and_generate(
        input={'text': query},
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': knowledge_base_id,
                'modelArn': model_arn,
                'retrievalConfiguration': {
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                },
                'generationConfiguration': {
                    'inferenceConfig': {
                        'textInferenceConfig': {
                            'maxTokens': 1000,
                            'temperature': 0.0  # Lower temp for factual responses
                        }
                    }
                }
            }
        }
    )

    # Extract response and citations
    output = response.get('output', {})
    citations = response.get('citations', [])

    result = {
        'response_text': output.get('text', ''),
        'citations': [],
        'sources_used': set()
    }

    # Process each citation
    for citation in citations:
        generated_span = citation.get('generatedResponsePart', {}).get('textResponsePart', {})

        for reference in citation.get('retrievedReferences', []):
            content = reference.get('content', {})
            location = reference.get('location', {})
            metadata = reference.get('metadata', {})

            citation_info = {
                'response_segment': {
                    'text': generated_span.get('text', ''),
                    'start': generated_span.get('span', {}).get('start'),
                    'end': generated_span.get('span', {}).get('end')
                },
                'source': {
                    'uri': location.get('s3Location', {}).get('uri', ''),
                    'type': location.get('type', ''),
                    'retrieved_text': content.get('text', '')[:500]  # Truncate for display
                },
                'metadata': metadata,
                'score': reference.get('score', 0)
            }

            result['citations'].append(citation_info)
            result['sources_used'].add(citation_info['source']['uri'])

    result['sources_used'] = list(result['sources_used'])
    return result


def format_response_with_inline_citations(result: Dict) -> str:
    """
    Format response with inline numbered citations.
    """
    response_text = result['response_text']
    citations = result['citations']

    # Build citation mapping
    source_numbers = {}
    for i, source in enumerate(result['sources_used'], 1):
        source_numbers[source] = i

    # Add citation numbers to response (simplified - real implementation would use spans)
    formatted_response = response_text

    # Build references section
    references = "\n\n---\n**Sources:**\n"
    for source, num in source_numbers.items():
        # Extract filename from S3 URI
        filename = source.split('/')[-1] if source else 'Unknown'
        references += f"[{num}] {filename}\n"

    return formatted_response + references


def retrieve_with_relevance_filter(
    knowledge_base_id: str,
    query: str,
    min_relevance_score: float = 0.5
) -> List[Dict]:
    """
    Retrieve documents and filter by relevance score.
    """
    response = bedrock_agent_runtime.retrieve(
        knowledgeBaseId=knowledge_base_id,
        retrievalQuery={'text': query},
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': 10  # Retrieve more, then filter
            }
        }
    )

    # Filter by relevance score
    high_relevance_results = []
    for result in response.get('retrievalResults', []):
        score = result.get('score', 0)
        if score >= min_relevance_score:
            high_relevance_results.append({
                'content': result.get('content', {}).get('text', ''),
                'source_uri': result.get('location', {}).get('s3Location', {}).get('uri', ''),
                'score': score,
                'metadata': result.get('metadata', {})
            })

    return high_relevance_results


# Example usage
result = retrieve_and_generate_with_citations(
    knowledge_base_id='KB123456',
    model_arn='arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0',
    query='What are the return policy requirements for electronics?'
)

print("== Response ==")
print(result['response_text'])
print(f"\n== Sources Used ({len(result['sources_used'])}) ==")
for source in result['sources_used']:
    print(f"  - {source}")

# Format with inline citations
formatted = format_response_with_inline_citations(result)
print("\n== Formatted Response ==")
print(formatted)