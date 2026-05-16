import boto3
import json

bedrock = boto3.client('bedrock-runtime')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

def expand_query(original_query, num_variations=3):
    """
    Generate query variations to improve retrieval recall.
    """
    prompt = f"""Generate {num_variations} alternative phrasings of this search query.
Each variation should capture the same intent but use different words.

Original query: {original_query}

Return only the variations, one per line, without numbering or explanations."""

    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 256,
            'temperature': 0.7
        })
    )

    result = json.loads(response['body'].read())
    variations = result['content'][0]['text'].strip().split('\n')

    return [original_query] + [v.strip() for v in variations if v.strip()]


def multi_query_retrieve(query, knowledge_base_id, k_per_query=5):
    """
    Retrieve using multiple query variations and merge results.
    """
    queries = expand_query(query)
    all_results = {}

    for q in queries:
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=knowledge_base_id,
            retrievalQuery={'text': q},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': k_per_query
                }
            }
        )

        for result in response['retrievalResults']:
            doc_id = result['location']['s3Location']['uri']
            if doc_id not in all_results or result['score'] > all_results[doc_id]['score']:
                all_results[doc_id] = result

    # Sort by score and return
    sorted_results = sorted(all_results.values(), key=lambda x: x['score'], reverse=True)
    return sorted_results


# Example
# Original: "vacation policy"
# Expanded: ["vacation policy", "time off rules", "PTO guidelines", "leave entitlement"]
# Retrieves from all variations, deduplicates, returns best scores