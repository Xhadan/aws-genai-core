import boto3
import json
from datetime import datetime
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from datasets import Dataset

def evaluate_rag_batch(
    questions: list,
    answers: list,
    contexts: list,
    llm,
    embeddings
) -> dict:
    """Evaluate a batch of RAG responses."""

    dataset = Dataset.from_dict({
        'question': questions,
        'answer': answers,
        'contexts': contexts
    })

    results = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision],
        llm=llm,
        embeddings=embeddings
    )

    return {
        'timestamp': datetime.utcnow().isoformat(),
        'sample_count': len(questions),
        'metrics': {
            'faithfulness': float(results['faithfulness']),
            'answer_relevancy': float(results['answer_relevancy']),
            'context_precision': float(results['context_precision'])
        }
    }

def publish_ragas_metrics(metrics: dict, namespace: str = 'RAG/Quality'):
    """Publish RAGAS metrics to CloudWatch."""

    cloudwatch = boto3.client('cloudwatch')

    metric_data = []
    for metric_name, value in metrics['metrics'].items():
        metric_data.append({
            'MetricName': metric_name.replace('_', ' ').title(),
            'Value': value,
            'Unit': 'None',
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': 'Pipeline', 'Value': 'ProductionRAG'}
            ]
        })

    cloudwatch.put_metric_data(
        Namespace=namespace,
        MetricData=metric_data
    )

    print(f"Published {len(metric_data)} metrics to CloudWatch")

def check_quality_thresholds(metrics: dict, thresholds: dict) -> list:
    """Check if metrics meet quality thresholds."""

    alerts = []
    for metric, threshold in thresholds.items():
        if metrics['metrics'].get(metric, 0) < threshold:
            alerts.append({
                'metric': metric,
                'value': metrics['metrics'][metric],
                'threshold': threshold
            })

    return alerts

# Example: Quality gates
thresholds = {
    'faithfulness': 0.8,
    'answer_relevancy': 0.75,
    'context_precision': 0.7
}

# metrics = evaluate_rag_batch(questions, answers, contexts, llm, embeddings)
# alerts = check_quality_thresholds(metrics, thresholds)
# if alerts:
#     send_alert(alerts)
# publish_ragas_metrics(metrics)