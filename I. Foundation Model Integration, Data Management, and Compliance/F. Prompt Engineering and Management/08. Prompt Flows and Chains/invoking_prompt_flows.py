import boto3
import json

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

def invoke_flow(flow_id, flow_alias_id, input_data):
    """Invoke a Bedrock Prompt Flow."""

    response = bedrock_agent_runtime.invoke_flow(
        flowIdentifier=flow_id,
        flowAliasIdentifier=flow_alias_id,
        inputs=[
            {
                "nodeName": "FlowInput",
                "nodeOutputName": "document",
                "content": {
                    "document": input_data
                }
            }
        ]
    )

    # Collect streaming response
    result = ""
    for event in response['responseStream']:
        if 'flowOutputEvent' in event:
            result = event['flowOutputEvent']['content']['document']

    return result


def invoke_flow_with_tracing(flow_id, flow_alias_id, input_data):
    """Invoke flow with execution tracing for debugging."""

    response = bedrock_agent_runtime.invoke_flow(
        flowIdentifier=flow_id,
        flowAliasIdentifier=flow_alias_id,
        inputs=[
            {
                "nodeName": "FlowInput",
                "nodeOutputName": "document",
                "content": {
                    "document": input_data
                }
            }
        ],
        enableTrace=True  # Enable execution tracing
    )

    result = ""
    traces = []

    for event in response['responseStream']:
        if 'flowOutputEvent' in event:
            result = event['flowOutputEvent']['content']['document']
        elif 'flowTraceEvent' in event:
            traces.append(event['flowTraceEvent'])

    return {
        'result': result,
        'traces': traces
    }


# Example usage
result = invoke_flow(
    flow_id="FLOW_ID",
    flow_alias_id="ALIAS_ID",
    input_data="How do I configure auto-scaling for my Lambda function?"
)

print(f"Response: {result}")

# With tracing
traced_result = invoke_flow_with_tracing(
    flow_id="FLOW_ID",
    flow_alias_id="ALIAS_ID",
    input_data="I'm unhappy with the response time of your service"
)

print(f"Response: {traced_result['result']}")
print(f"Execution trace: {json.dumps(traced_result['traces'], indent=2)}")