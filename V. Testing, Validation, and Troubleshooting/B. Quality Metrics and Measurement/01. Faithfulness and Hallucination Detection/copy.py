import boto3
import json
from datetime import datetime

bedrock_runtime = boto3.client('bedrock-runtime')
cloudwatch = boto3.client('cloudwatch')

class FaithfulnessMonitor:
    """Monitor faithfulness in production RAG responses."""

    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold

    def quick_faithfulness_check(
        self,
        response: str,
        context: str
    ) -> Dict:
        """Fast faithfulness check for real-time monitoring."""

        prompt = f"""Rate the faithfulness of the response to the context on a scale of 0 to 1.
Faithfulness means all claims in the response are supported by the context.

Context: {context[:2000]}

Response: {response[:1000]}

Return only JSON:
{{"faithfulness_score": 0.0-1.0, "has_unsupported_claims": true/false}}
"""

        result = bedrock_runtime.converse(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',  # Fast model
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'maxTokens': 100, 'temperature': 0.0}
        )

        return json.loads(result['output']['message']['content'][0]['text'])

    def monitor_and_log(
        self,
        response: str,
        context: str,
        request_id: str
    ) -> Dict:
        """Check faithfulness and publish metrics."""

        check = self.quick_faithfulness_check(response, context)

        # Publish to CloudWatch
        cloudwatch.put_metric_data(
            Namespace='RAG/Quality',
            MetricData=[
                {
                    'MetricName': 'Faithfulness',
                    'Value': check['faithfulness_score'],
                    'Unit': 'None',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'Pipeline', 'Value': 'ProductionRAG'}
                    ]
                },
                {
                    'MetricName': 'HallucinationDetected',
                    'Value': 1 if check['has_unsupported_claims'] else 0,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'Pipeline', 'Value': 'ProductionRAG'}
                    ]
                }
            ]
        )

        # Flag for review if below threshold
        if check['faithfulness_score'] < self.threshold:
            self.flag_for_review(request_id, response, context, check)

        return check

    def flag_for_review(
        self,
        request_id: str,
        response: str,
        context: str,
        check: Dict
    ):
        """Flag low-faithfulness responses for human review."""
        # Could send to SQS, DynamoDB, or alerting system
        print(f"FLAGGED: Request {request_id} - Score: {check['faithfulness_score']}")