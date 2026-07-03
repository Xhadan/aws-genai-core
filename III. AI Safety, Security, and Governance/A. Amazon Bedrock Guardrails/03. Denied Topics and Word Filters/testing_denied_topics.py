import boto3

bedrock_runtime = boto3.client('bedrock-runtime')

def test_denied_topics(guardrail_id, guardrail_version, test_prompts):
    """
    Test prompts against denied topics configuration.
    """
    results = []

    for prompt in test_prompts:
        response = bedrock_runtime.apply_guardrail(
            guardrailIdentifier=guardrail_id,
            guardrailVersion=guardrail_version,
            source='INPUT',
            content=[{'text': {'text': prompt}}]
        )

        result = {
            'prompt': prompt,
            'action': response['action'],
            'topics_matched': []
        }

        # Extract matched topics from assessments
        for assessment in response.get('assessments', []):
            topic_policy = assessment.get('topicPolicy', {})
            for topic in topic_policy.get('topics', []):
                if topic.get('action') = 'BLOCKED':
                    result['topics_matched'].append(topic.get('name'))

        results.append(result)

    return results

# Test various phrasings of blocked topics
test_prompts = [
    "How does your product compare to CompetitorX?",  # Direct mention
    "What alternatives to your service exist?",  # Paraphrased
    "Should I buy Tesla stock right now?",  # Investment advice
    "What do you think about the stock market?",  # Should pass
    "I have a headache, what medicine should I take?",  # Medical
    "Tell me about headache remedies in general"  # Should pass
]

results = test_denied_topics('your-guardrail-id', '1', test_prompts)
for r in results:
    status = 'BLOCKED' if r['action'] = 'GUARDRAIL_INTERVENED' else 'PASSED'
    topics = ', '.join(r['topics_matched']) if r['topics_matched'] else 'None'
    print(f"{status}: '{r['prompt'][:50]}...' - Topics: {topics}")