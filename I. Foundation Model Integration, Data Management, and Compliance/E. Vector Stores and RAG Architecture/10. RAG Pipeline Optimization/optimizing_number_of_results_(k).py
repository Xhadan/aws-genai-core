import boto3
from collections import defaultdict

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

def evaluate_k_values(knowledge_base_id, test_queries, k_values=[3, 5, 10, 15, 20]):
    """
    Evaluate different k values to find optimal retrieval count.
    """
    results = defaultdict(list)

    for query_data in test_queries:
        query = query_data['query']
        relevant_docs = set(query_data['relevant_doc_ids'])

        for k in k_values:
            response = bedrock_agent_runtime.retrieve(
                knowledgeBaseId=knowledge_base_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': k
                    }
                }
            )

            # Calculate metrics
            retrieved_ids = set([
                r['location']['s3Location']['uri']
                for r in response['retrievalResults']
            ])

            precision = len(retrieved_ids & relevant_docs) / len(retrieved_ids) if retrieved_ids else 0
            recall = len(retrieved_ids & relevant_docs) / len(relevant_docs) if relevant_docs else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

            results[k].append({
                'precision': precision,
                'recall': recall,
                'f1': f1
            })

    # Average metrics per k
    summary = {}
    for k, metrics in results.items():
        summary[k] = {
            'avg_precision': sum(m['precision'] for m in metrics) / len(metrics),
            'avg_recall': sum(m['recall'] for m in metrics) / len(metrics),
            'avg_f1': sum(m['f1'] for m in metrics) / len(metrics)
        }

    return summary

# Example: Find optimal k
test_queries = [
    {'query': 'What is the vacation policy?', 'relevant_doc_ids': ['doc1', 'doc3']},
    {'query': 'How to submit expenses?', 'relevant_doc_ids': ['doc5', 'doc7', 'doc8']}
]

k_results = evaluate_k_values('KB12345678', test_queries)
for k, metrics in k_results.items():
    print(f"k={k}: Precision={metrics['avg_precision']:.2f}, Recall={metrics['avg_recall']:.2f}, F1={metrics['avg_f1']:.2f}")