def create_rag_flow(
    service: PromptFlowService,
    name: str,
    knowledge_base_id: str,
    execution_role_arn: str
) -> Dict[str, Any]:
    """Create RAG flow with knowledge base retrieval."""

    flow_definition = {
        "nodes": [
            {
                "name": "Input",
                "type": "Input",
                "outputs": [
                    {"name": "question", "type": "String"}
                ]
            },
            {
                "name": "KBRetrieval",
                "type": "KnowledgeBase",
                "configuration": {
                    "knowledgeBase": {
                        "knowledgeBaseId": knowledge_base_id,
                        "modelId": "anthropic.claude-3-sonnet-20240229-v1:0"
                    }
                },
                "inputs": [
                    {"name": "retrievalQuery", "type": "String", "expression": "$.data"}
                ],
                "outputs": [
                    {"name": "retrievedReferences", "type": "Array"}
                ]
            },
            {
                "name": "AnswerGenerator",
                "type": "Prompt",
                "configuration": {
                    "prompt": {
                        "sourceConfiguration": {
                            "inline": {
                                "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
                                "templateType": "TEXT",
                                "templateConfiguration": {
                                    "text": {
                                        "text": """Based on the following context, answer the question.

Context:
{{context}}

Question: {{question}}

Provide a comprehensive answer with citations."""
                                    }
                                },
                                "inferenceConfiguration": {
                                    "text": {
                                        "maxTokens": 2000,
                                        "temperature": 0.3
                                    }
                                }
                            }
                        }
                    }
                },
                "inputs": [
                    {"name": "context", "type": "String", "expression": "$.data"},
                    {"name": "question", "type": "String", "expression": "$.data"}
                ]
            },
            {
                "name": "Output",
                "type": "Output",
                "inputs": [
                    {"name": "answer", "type": "String", "expression": "$.data"},
                    {"name": "sources", "type": "Array", "expression": "$.data"}
                ]
            }
        ],
        "connections": [
            {
                "source": "Input",
                "target": "KBRetrieval",
                "configuration": {
                    "data": {
                        "sourceOutput": "question",
                        "targetInput": "retrievalQuery"
                    }
                }
            },
            {
                "source": "KBRetrieval",
                "target": "AnswerGenerator",
                "configuration": {
                    "data": {
                        "sourceOutput": "retrievedReferences",
                        "targetInput": "context"
                    }
                }
            },
            {
                "source": "Input",
                "target": "AnswerGenerator",
                "configuration": {
                    "data": {
                        "sourceOutput": "question",
                        "targetInput": "question"
                    }
                }
            },
            {
                "source": "AnswerGenerator",
                "target": "Output"
            },
            {
                "source": "KBRetrieval",
                "target": "Output",
                "configuration": {
                    "data": {
                        "sourceOutput": "retrievedReferences",
                        "targetInput": "sources"
                    }
                }
            }
        ]
    }

    return service.bedrock_agent.create_flow(
        name=name,
        description="RAG flow with knowledge base retrieval",
        executionRoleArn=execution_role_arn,
        definition=flow_definition
    )