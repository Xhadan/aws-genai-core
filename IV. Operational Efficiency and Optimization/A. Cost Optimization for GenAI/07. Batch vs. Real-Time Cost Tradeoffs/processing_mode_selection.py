import boto3
from typing import List, Dict
from enum import Enum
from dataclasses import dataclass

class ProcessingMode(Enum):
    REALTIME = "realtime"
    STREAMING = "streaming"
    ASYNC_QUEUE = "async_queue"
    BATCH = "batch"

@dataclass
class WorkloadCharacteristics:
    request_count: int
    latency_requirement_seconds: float
    cost_sensitivity: str  # 'low', 'medium', 'high'
    interactivity_required: bool
    deadline_hours: float = None

class ProcessingModeSelector:
    """Select optimal processing mode based on workload characteristics"""

    def select_mode(self, workload: WorkloadCharacteristics) -> ProcessingMode:
        """
        Select processing mode based on workload characteristics.

        Decision Logic:
        1. Interactive + low latency = Streaming
        2. Interactive + moderate latency = Realtime
        3. Non-interactive + high volume + cost sensitive = Batch
        4. Non-interactive + moderate latency = Async Queue
        """

        # Interactive workloads need real-time
        if workload.interactivity_required:
            if workload.latency_requirement_seconds < 2:
                return ProcessingMode.STREAMING
            else:
                return ProcessingMode.REALTIME

        # Non-interactive workloads
        if workload.request_count >= 1000 and workload.cost_sensitivity = 'high':
            # Large volume + cost sensitive = batch
            if workload.deadline_hours is None or workload.deadline_hours >= 24:
                return ProcessingMode.BATCH

        if workload.latency_requirement_seconds > 60:
            # Can tolerate delay = async queue
            return ProcessingMode.ASYNC_QUEUE

        # Default to realtime
        return ProcessingMode.REALTIME

    def estimate_cost(
        self,
        mode: ProcessingMode,
        input_tokens: int,
        output_tokens: int,
        model_id: str = 'anthropic.claude-3-haiku-20240307-v1:0'
    ) -> float:
        """Estimate cost for processing mode"""

        # Base pricing (Haiku as example)
        base_input_cost = 0.00025  # per 1K tokens
        base_output_cost = 0.00125  # per 1K tokens

        base_cost = (
            (input_tokens / 1000) * base_input_cost +
            (output_tokens / 1000) * base_output_cost
        )

        # Apply discount for batch
        if mode = ProcessingMode.BATCH:
            return base_cost * 0.5  # 50% discount

        return base_cost


class HybridProcessor:
    """Process requests using optimal mode"""

    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime')
        self.selector = ProcessingModeSelector()

    def process(
        self,
        requests: List[Dict],
        workload: WorkloadCharacteristics
    ) -> List[Dict]:
        """Process requests using selected mode"""

        mode = self.selector.select_mode(workload)
        print(f"Selected processing mode: {mode.value}")

        if mode = ProcessingMode.REALTIME:
            return self._process_realtime(requests)
        elif mode = ProcessingMode.STREAMING:
            return self._process_streaming(requests)
        elif mode = ProcessingMode.ASYNC_QUEUE:
            return self._process_async(requests)
        elif mode = ProcessingMode.BATCH:
            return self._process_batch(requests)

    def _process_realtime(self, requests: List[Dict]) -> List[Dict]:
        """Process with synchronous API calls"""
        results = []

        for req in requests:
            response = self.bedrock.converse(
                modelId=req.get('model_id', 'anthropic.claude-3-haiku-20240307-v1:0'),
                messages=[{'role': 'user', 'content': [{'text': req['prompt']}]}],
                inferenceConfig={'maxTokens': req.get('max_tokens', 500)}
            )

            results.append({
                'id': req.get('id'),
                'response': response['output']['message']['content'][0]['text'],
                'mode': 'realtime'
            })

        return results

    def _process_streaming(self, requests: List[Dict]) -> List[Dict]:
        """Process with streaming for lower perceived latency"""
        results = []

        for req in requests:
            response = self.bedrock.converse_stream(
                modelId=req.get('model_id', 'anthropic.claude-3-haiku-20240307-v1:0'),
                messages=[{'role': 'user', 'content': [{'text': req['prompt']}]}],
                inferenceConfig={'maxTokens': req.get('max_tokens', 500)}
            )

            # Collect streamed response
            full_response = ""
            for event in response['stream']:
                if 'contentBlockDelta' in event:
                    full_response += event['contentBlockDelta']['delta']['text']

            results.append({
                'id': req.get('id'),
                'response': full_response,
                'mode': 'streaming'
            })

        return results

    def _process_async(self, requests: List[Dict]) -> List[Dict]:
        """Process via async queue (simplified - would use SQS in production)"""
        # In production, this would:
        # 1. Push to SQS
        # 2. Lambda processes from queue
        # 3. Results stored in DynamoDB/S3
        # Here we simulate with delayed processing

        import time
        results = []

        for req in requests:
            # Simulate async processing
            response = self.bedrock.converse(
                modelId=req.get('model_id', 'anthropic.claude-3-haiku-20240307-v1:0'),
                messages=[{'role': 'user', 'content': [{'text': req['prompt']}]}],
                inferenceConfig={'maxTokens': req.get('max_tokens', 500)}
            )

            results.append({
                'id': req.get('id'),
                'response': response['output']['message']['content'][0]['text'],
                'mode': 'async_queue'
            })

        return results

    def _process_batch(self, requests: List[Dict]) -> List[Dict]:
        """Process via batch inference"""
        # Would use BatchInferenceManager from previous example
        # Here we simulate the result structure

        print(f"Processing {len(requests)} requests via batch inference...")
        print("Note: In production, this would submit a batch job and return job ID")

        # Simulate batch processing
        results = []
        for req in requests:
            results.append({
                'id': req.get('id'),
                'response': f"[Batch processed] Response for: {req['prompt'][:50]}...",
                'mode': 'batch'
            })

        return results


# Example: Select processing mode based on workload
selector = ProcessingModeSelector()

# Scenario 1: Interactive chatbot
chatbot_workload = WorkloadCharacteristics(
    request_count=1,
    latency_requirement_seconds=1,
    cost_sensitivity='medium',
    interactivity_required=True
)
print(f"Chatbot: {selector.select_mode(chatbot_workload).value}")  # streaming

# Scenario 2: Document processing pipeline
pipeline_workload = WorkloadCharacteristics(
    request_count000,
    latency_requirement_seconds400,  # 24 hours acceptable
    cost_sensitivity='high',
    interactivity_requiredlse,
    deadline_hoursH
)
print(f"Pipeline: {selector.select_mode(pipeline_workload).value}")  # batch

# Scenario 3: Email generation
email_workload = WorkloadCharacteristics(
    request_count0,
    latency_requirement_seconds00,  # 5 minutes acceptable
    cost_sensitivity='medium',
    interactivity_requiredlse
)
print(f"Email: {selector.select_mode(email_workload).value}")  # async_queue