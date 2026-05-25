import boto3
import json

bedrock_agent = boto3.client('bedrock-agent')

def create_prompt_flow(name, description, flow_definition):
    """Create a Bedrock Prompt Flow."""

    response = bedrock_agent.create_flow(
        name=name,
        descriptionscription,
        executionRoleArn="arn:aws:iam::ACCOUNT:role/BedrockFlowRole",
        definition=flow_definition
    )

    return response['id'], response['arn']


def build_simple_flow():
    """Build a simple sequential flow definition."""

    flow_definition = {
        "nodes": [
            {
                "name": "FlowInput",
                "type": "Input",
                "configuration": {
                    "input": {}
                },
                "outputs": [
                    {
                        "name": "document",
                        "type": "String"
                    }
                ]
            },
            {
                "name": "ClassifyIntent",
                "type": "Prompt",
                "configuration": {
                    "prompt": {
                        "sourceConfiguration": {
                            "inline": {
                                "modelId": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                                "templateType": "TEXT",
                                "templateConfiguration": {
                                    "text": {
                                        "text": "Classify the intent of this query into one of: question, complaint, feedback, request.\n\nQuery: {{query}}\n\nIntent:",
                                        "inputVariables": [{"name": "query"}]
                                    }
                                }
                            }
                        }
                    }
                },
                "inputs": [
                    {
                        "name": "query",
                        "type": "String",
                        "expression": "$.data"
                    }
                ],
                "outputs": [
                    {
                        "name": "modelCompletion",
                        "type": "String"
                    }
                ]
            },
            {
                "name": "GenerateResponse",
                "type": "Prompt",
                "configuration": {
                    "prompt": {
                        "sourceConfiguration": {
                            "inline": {
                                "modelId": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                                "templateType": "TEXT",
                                "templateConfiguration": {
                                    "text": {
                                        "text": "Generate a helpful response for this {{intent}} about: {{query}}\n\nResponse:",
                                        "inputVariables": [
                                            {"name": "intent"},
                                            {"name": "query"}
                                        ]
                                    }
                                }
                            }
                        }
                    }
                },
                "inputs": [
                    {
                        "name": "intent",
                        "type": "String",
                        "expression": "$.data"
                    },
                    {
                        "name": "query",
                        "type": "String",
                        "expression": "$.data"
                    }
                ],
                "outputs": [
                    {
                        "name": "modelCompletion",
                        "type": "String"
                    }
                ]
            },
            {
                "name": "FlowOutput",
                "type": "Output",
                "configuration": {
                    "output": {}
                },
                "inputs": [
                    {
                        "name": "document",
                        "type": "String",
                        "expression": "$.data"
                    }
                ]
            }
        ],
        "connections": [
            {
                "name": "InputToClassify",
                "source": "FlowInput",
                "target": "ClassifyIntent",
                "type": "Data",
                "configuration": {
                    "data": {
                        "sourceOutput": "document",
                        "targetInput": "query"
                    }
                }
            },
            {
                "name": "ClassifyToGenerate",
                "source": "ClassifyIntent",
                "target": "GenerateResponse",
                "type": "Data",
                "configuration": {
                    "data": {
                        "sourceOutput": "modelCompletion",
                        "targetInput": "intent"
                    }
                }
            },
            {
                "name": "GenerateToOutput",
                "source": "GenerateResponse",
                "target": "FlowOutput",
                "type": "Data",
                "configuration": {
                    "data": {
                        "sourceOutput": "modelCompletion",
                        "targetInput": "document"
                    }
                }
            }
        ]
    }

    return flow_definition


# Create the flow
flow_def = build_simple_flow()
flow_id, flow_arn = create_prompt_flow(
    name="customer-support-flow",
    description="Classify intent and generate response",
    flow_definition=flow_def
)

print(f"Created flow: {flow_id}")