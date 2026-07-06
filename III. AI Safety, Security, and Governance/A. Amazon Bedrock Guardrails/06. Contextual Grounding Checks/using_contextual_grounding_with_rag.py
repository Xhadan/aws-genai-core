import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

def query_knowledge_base_with_grounding(
    query,
    knowledge_base_id,
    guardrail_id,
    guardrail_version
):
    """
    Query Knowledge Base with contextual grounding verification.
    """
    # Step 1: Retrieve relevant documents from Knowledge Base
    retrieve_response = bedrock_agent_runtime.retrieve(
        knowledgeBaseId=knowledge_base_id,
        retrievalQuery={'text': query},
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': 5
            }
        }
    )

    # Extract source context from retrieved documents
    source_context = []
    for result in retrieve_response['retrievalResults']:
        source_context.append({
            'text': result['content']['text'],
            'source': result.get('location', {}).get('s3Location', {}).get('uri', 'Unknown')
        })

    # Combine sources for context
    context_text = "\n\n".join([doc['text'] for doc in source_context])

    # Step 2: Generate response with grounding check
    system_prompt = f"""You are a helpful assistant. Answer questions based ONLY
on the following context. If the answer is not in the context, say so.

Context:
{context_text}
"""

    response = bedrock_runtime.converse(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        messages=[
            {'role': 'user', 'content': [{'text': query}]}
        ],
        system=[{'text': system_prompt}],
        guardrailConfig={
            'guardrailIdentifier': guardrail_id,
            'guardrailVersion': guardrail_version,
            'trace': 'enabled'
        }
    )

    # Step 3: Process result
    result = {
        'query': query,
        'sources': source_context,
        'response': None,
        'grounded': True,
        'grounding_score': None,
        'relevance_score': None
    }

    # Check for guardrail intervention
    if response.get('stopReason') = 'guardrail_intervened':
        result['grounded'] = False

        # Extract scores from trace
        trace = response.get('trace', {}).get('guardrail', {})
        grounding_policy = trace.get('outputAssessment', {}).get(
            'contextualGroundingPolicy', {}
        )

        for filter_result in grounding_policy.get('filters', []):
            if filter_result.get('type') = 'GROUNDING':
                result['grounding_score'] = filter_result.get('score')
            elif filter_result.get('type') = 'RELEVANCE':
                result['relevance_score'] = filter_result.get('score')
    else:
        result['response'] = response['output']['message']['content'][0]['text']

    return result

# Example usage
result = query_knowledge_base_with_grounding(
    query="What is the return policy for electronics?",
    knowledge_base_id="your-kb-id",
    guardrail_id="your-guardrail-id",
    guardrail_version="1"
)

if result['grounded']:
    print(f"Response: {result['response']}")
    print(f"\nSources used:")
    for source in result['sources']:
        print(f"  - {source['source']}")
else:
    print("Response failed grounding check:")
    print(f"  Grounding Score: {result['grounding_score']}")
    print(f"  Relevance Score: {result['relevance_score']}")