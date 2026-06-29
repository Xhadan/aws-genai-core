import boto3
import json
from typing import Dict, Any, Generator

class FlowInvoker:
    """Invoke Bedrock Prompt Flows."""

    def __init__(self, region_name: str = "us-east-1"):
        self.runtime = boto3.client(
            "bedrock-agent-runtime",
            region_name=region_name
        )

    def invoke_flow(
        self,
        flow_id: str,
        flow_alias_id: str,
        inputs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Invoke flow synchronously."""

        response = self.runtime.invoke_flow(
            flowIdentifier=flow_id,
            flowAliasIdentifier=flow_alias_id,
            inputs=inputs
        )

        # Process response stream
        result = None
        for event in response["responseStream"]:
            if "flowOutputEvent" in event:
                result = event["flowOutputEvent"]
            elif "flowCompletionEvent" in event:
                completion = event["flowCompletionEvent"]
                print(f"Flow completed: {completion['completionReason']}")

        return result

    def invoke_flow_streaming(
        self,
        flow_id: str,
        flow_alias_id: str,
        inputs: List[Dict[str, Any]]
    ) -> Generator[Dict[str, Any], None, None]:
        """Invoke flow with streaming response."""

        response = self.runtime.invoke_flow(
            flowIdentifier=flow_id,
            flowAliasIdentifier=flow_alias_id,
            inputs=inputs
        )

        for event in response["responseStream"]:
            if "flowOutputEvent" in event:
                yield {
                    "type": "output",
                    "data": event["flowOutputEvent"]
                }
            elif "flowCompletionEvent" in event:
                yield {
                    "type": "completion",
                    "reason": event["flowCompletionEvent"]["completionReason"]
                }
            elif "flowTraceEvent" in event:
                yield {
                    "type": "trace",
                    "data": event["flowTraceEvent"]
                }


# Usage example
invoker = FlowInvoker()

# Invoke summarization flow
result = invoker.invoke_flow(
    flow_id="FLOW123ABC",
    flow_alias_id="ALIAS456DEF",
    inputs=[
        {
            "nodeName": "InputNode",
            "nodeOutputName": "document",
            "content": {
                "document": "This is a long document that needs summarization..."
            }
        }
    ]
)

print(f"Summary: {result['content']}")