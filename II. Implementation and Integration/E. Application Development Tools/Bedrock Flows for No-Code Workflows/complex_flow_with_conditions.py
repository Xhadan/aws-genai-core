def create_conditional_flow(
    service: PromptFlowService,
    name: str,
    execution_role_arn: str
) -> Dict[str, Any]:
    """Create flow with conditional branching."""

    flow_definition = {
        "nodes": [
            {
                "name": "Input",
                "type": "Input",
                "outputs": [
                    {"name": "query", "type": "String"},
                    {"name": "category", "type": "String"}
                ]
            },
            {
                "name": "CategoryRouter",
                "type": "Condition",
                "configuration": {
                    "condition": {
                        "conditions": [
                            {
                                "name": "IsTechnical",
                                "expression": "category = 'technical'"
                            },
                            {
                                "name": "IsGeneral",
                                "expression": "category = 'general'"
                            }
                        ]
                    }
                },
                "inputs": [
                    {"name": "category", "type": "String", "expression": "$.data"}
                ]
            },
            {
                "name": "TechnicalPrompt",
                "type": "Prompt",
                "configuration": {
                    "prompt": {
                        "sourceConfiguration": {
                            "inline": {
                                "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
                                "templateType": "TEXT",
                                "templateConfiguration": {
                                    "text": {
                                        "text": "As a technical expert, answer: {{query}}"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            {
                "name": "GeneralPrompt",
                "type": "Prompt",
                "configuration": {
                    "prompt": {
                        "sourceConfiguration": {
                            "inline": {
                                "modelId": "anthropic.claude-3-haiku-20240307-v1:0",
                                "templateType": "TEXT",
                                "templateConfiguration": {
                                    "text": {
                                        "text": "Answer this question helpfully: {{query}}"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            {
                "name": "CollectorNode",
                "type": "Collector",
                "configuration": {
                    "collector": {}
                }
            },
            {
                "name": "Output",
                "type": "Output"
            }
        ],
        "connections": [
            # Input to condition
            {
                "source": "Input",
                "target": "CategoryRouter",
                "configuration": {
                    "data": {
                        "sourceOutput": "category",
                        "targetInput": "category"
                    }
                }
            },
            # Condition to technical prompt
            {
                "source": "CategoryRouter",
                "target": "TechnicalPrompt",
                "type": "Conditional",
                "configuration": {
                    "conditional": {
                        "condition": "IsTechnical"
                    }
                }
            },
            # Condition to general prompt
            {
                "source": "CategoryRouter",
                "target": "GeneralPrompt",
                "type": "Conditional",
                "configuration": {
                    "conditional": {
                        "condition": "IsGeneral"
                    }
                }
            },
            # Both prompts to collector
            {
                "source": "TechnicalPrompt",
                "target": "CollectorNode"
            },
            {
                "source": "GeneralPrompt",
                "target": "CollectorNode"
            },
            # Collector to output
            {
                "source": "CollectorNode",
                "target": "Output"
            }
        ]
    }

    return service.bedrock_agent.create_flow(
        name=name,
        executionRoleArn=execution_role_arn,
        definition=flow_definition
    )