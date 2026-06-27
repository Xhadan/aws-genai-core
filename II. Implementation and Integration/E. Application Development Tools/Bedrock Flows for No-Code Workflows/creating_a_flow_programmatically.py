import boto3
import json
from typing import Dict, Any, List

class PromptFlowService:
    """Service for managing Bedrock Prompt Flows."""

    def __init__(self, region_name: str = "us-east-1"):
        self.bedrock_agent = boto3.client(
            "bedrock-agent",
            region_name=region_name
        )
        self.bedrock_agent_runtime = boto3.client(
            "bedrock-agent-runtime",
            region_name=region_name
        )

    def create_flow(
        self,
        name: str,
        description: str,
        execution_role_arn: str
    ) -> Dict[str, Any]:
        """Create a new prompt flow."""

        # Define flow definition with nodes
        flow_definition = {
            "nodes": [
                {
                    "name": "InputNode",
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
                    "name": "PromptNode",
                    "type": "Prompt",
                    "configuration": {
                        "prompt": {
                            "sourceConfiguration": {
                                "inline": {
                                    "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
                                    "templateType": "TEXT",
                                    "templateConfiguration": {
                                        "text": {
                                            "text": "Summarize the following document:\n\n{{document}}"
                                        }
                                    },
                                    "inferenceConfiguration": {
                                        "text": {
                                            "maxTokens": 1000,
                                            "temperature": 0.7
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "inputs": [
                        {
                            "name": "document",
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
                    "name": "OutputNode",
                    "type": "Output",
                    "configuration": {
                        "output": {}
                    },
                    "inputs": [
                        {
                            "name": "summary",
                            "type": "String",
                            "expression": "$.data"
                        }
                    ]
                }
            ],
            "connections": [
                {
                    "name": "InputToPrompt",
                    "source": "InputNode",
                    "target": "PromptNode",
                    "type": "Data",
                    "configuration": {
                        "data": {
                            "sourceOutput": "document",
                            "targetInput": "document"
                        }
                    }
                },
                {
                    "name": "PromptToOutput",
                    "source": "PromptNode",
                    "target": "OutputNode",
                    "type": "Data",
                    "configuration": {
                        "data": {
                            "sourceOutput": "modelCompletion",
                            "targetInput": "summary"
                        }
                    }
                }
            ]
        }

        response = self.bedrock_agent.create_flow(
            name=name,
            descriptionscription,
            executionRoleArn=execution_role_arn,
            definition=flow_definition
        )

        return {
            "flow_id": response["id"],
            "flow_arn": response["arn"],
            "status": response["status"],
            "version": response.get("version", "DRAFT")
        }

    def prepare_flow(self, flow_id: str) -> Dict[str, Any]:
        """Prepare flow for execution (validate and compile)."""

        response = self.bedrock_agent.prepare_flow(
            flowIdentifier=flow_id
        )

        return {
            "flow_id": response["id"],
            "status": response["status"]
        }

    def create_flow_alias(
        self,
        flow_id: str,
        alias_name: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """Create alias for flow version."""

        response = self.bedrock_agent.create_flow_alias(
            flowIdentifier=flow_id,
            name=alias_name,
            descriptionscription,
            routingConfiguration=[
                {
                    "flowVersion": "DRAFT"  # Or specific version
                }
            ]
        )

        return {
            "alias_id": response["id"],
            "alias_arn": response["arn"],
            "name": response["name"]
        }