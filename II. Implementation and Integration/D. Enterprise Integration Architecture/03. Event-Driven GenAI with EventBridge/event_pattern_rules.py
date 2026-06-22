import boto3
import json

events = boto3.client('events')

def create_genai_event_rules():
    """Create EventBridge rules for GenAI event routing."""

    # Rule 1: Route high-token requests to cost monitoring
    events.put_rule(
        Name='high-token-usage',
        EventBusName='genai-events',
        EventPattern=json.dumps({
            "source": ["genai.inference"],
            "detail-type": ["Inference Completed"],
            "detail": {
                "output_tokens": [{
                    "numeric": [">=", 2000]
                }]
            }
        }),
        State='ENABLED',
        Description='Route high token usage events for cost monitoring'
    )

    events.put_targets(
        Rule='high-token-usage',
        EventBusName='genai-events',
        Targets=[{
            'Id': 'cost-monitor',
            'Arn': 'arn:aws:lambda:us-east-1:123456789012:function:cost-monitor',
            'InputTransformer': {
                'InputPathsMap': {
                    'requestId': '$.detail.request_id',
                    'tokens': '$.detail.output_tokens',
                    'model': '$.detail.model_id'
                },
                'InputTemplate': '{"alert_type": "high_usage", "request_id": <requestId>, "tokens": <tokens>, "model": <model>}'
            }
        }]
    )

    # Rule 2: Route guardrail events to security team
    events.put_rule(
        Name='guardrail-alerts',
        EventBusName='genai-events',
        EventPattern=json.dumps({
            "source": ["genai.guardrails"],
            "detail-type": ["Guardrail Triggered"],
            "detail": {
                "action": ["BLOCKED", "GUARDRAIL_INTERVENED"]
            }
        }),
        State='ENABLED',
        Description='Alert on blocked content'
    )

    events.put_targets(
        Rule='guardrail-alerts',
        EventBusName='genai-events',
        Targets=[
            {
                'Id': 'security-sns',
                'Arn': 'arn:aws:sns:us-east-1:123456789012:security-alerts'
            },
            {
                'Id': 'audit-log',
                'Arn': 'arn:aws:lambda:us-east-1:123456789012:function:audit-logger'
            }
        ]
    )

    # Rule 3: Fan-out document processing events
    events.put_rule(
        Name='document-processed-fanout',
        EventBusName='genai-events',
        EventPattern=json.dumps({
            "source": ["genai.document-processor"],
            "detail-type": ["Document Processed"],
            "detail": {
                "status": ["completed"]
            }
        }),
        State='ENABLED',
        Description='Fan out document processing completion'
    )

    events.put_targets(
        Rule='document-processed-fanout',
        EventBusName='genai-events',
        Targets=[
            {'Id': 'indexer', 'Arn': 'arn:aws:lambda:...:function:index-document'},
            {'Id': 'notifier', 'Arn': 'arn:aws:lambda:...:function:notify-user'},
            {'Id': 'analytics', 'Arn': 'arn:aws:sqs:...:analytics-queue'}
        ]
    )

    print("EventBridge rules created successfully")

# Input transformer examples
INPUT_TRANSFORMER_EXAMPLES = {
    # Transform event for Bedrock-compatible format
    "bedrock_prompt": {
        "InputPathsMap": {
            "content": "$.detail.document_text",
            "taskType": "$.detail.task_type"
        },
        "InputTemplate": '{"prompt": "Perform <taskType> on this content: <content>"}'
    },

    # Transform for notification
    "notification": {
        "InputPathsMap": {
            "docName": "$.detail.object.key",
            "bucket": "$.detail.bucket.name"
        },
        "InputTemplate": '"Document <docName> in bucket <bucket> has been processed"'
    }
}