import boto3
import json
from datetime import datetime
from typing import Optional

events = boto3.client('events')

class GenAIEventPublisher:
    """
    Publisher for GenAI-related events to EventBridge.
    """

    def __init__(self, event_bus_name: str = 'genai-events'):
        self.event_bus = event_bus_name

    def publish_inference_request(
        self,
        request_id: str,
        model_id: str,
        prompt_type: str,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """Publish when an inference request is submitted."""
        self._put_event(
            source='genai.inference',
            detail_type='Inference Requested',
            detail={
                'request_id': request_id,
                'model_id': model_id,
                'prompt_type': prompt_type,
                'user_id': user_id,
                'metadata': metadata or {},
                'timestamp': datetime.utcnow().isoformat()
            }
        )

    def publish_inference_completed(
        self,
        request_id: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        success: bool = True
    ):
        """Publish when inference completes."""
        self._put_event(
            source='genai.inference',
            detail_type='Inference Completed',
            detail={
                'request_id': request_id,
                'model_id': model_id,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'latency_ms': latency_ms,
                'success': success,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

    def publish_content_generated(
        self,
        content_type: str,
        content_id: str,
        model_id: str,
        quality_score: Optional[float] = None
    ):
        """Publish when content is generated."""
        self._put_event(
            source='genai.content',
            detail_type='Content Generated',
            detail={
                'content_type': content_type,
                'content_id': content_id,
                'model_id': model_id,
                'quality_score': quality_score,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

    def publish_guardrail_triggered(
        self,
        request_id: str,
        guardrail_id: str,
        action: str,
        reason: str
    ):
        """Publish when a guardrail is triggered."""
        self._put_event(
            source='genai.guardrails',
            detail_type='Guardrail Triggered',
            detail={
                'request_id': request_id,
                'guardrail_id': guardrail_id,
                'action': action,
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

    def _put_event(self, source: str, detail_type: str, detail: dict):
        """Put event to EventBridge."""
        response = events.put_events(
            Entries=[{
                'Source': source,
                'DetailType': detail_type,
                'Detail': json.dumps(detail),
                'EventBusName': self.event_bus
            }]
        )

        if response.get('FailedEntryCount', 0) > 0:
            print(f"Failed to publish event: {response['Entries']}")

# Usage
publisher = GenAIEventPublisher()

# Publish inference request
publisher.publish_inference_request(
    request_id='req-123',
    model_id='anthropic.claude-3-sonnet-20240229-v1:0',
    prompt_type='summarization',
    user_id='user-456'
)

# Later, publish completion
publisher.publish_inference_completed(
    request_id='req-123',
    model_id='anthropic.claude-3-sonnet-20240229-v1:0',
    input_tokensP0,
    output_tokens 0,
    latency_ms00.5
)