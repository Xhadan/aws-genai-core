import boto3
from mcp.server import Server
from mcp.types import Tool, TextContent
import json

server = Server("bedrock-bridge")
bedrock_runtime = boto3.client('bedrock-agent-runtime')

@server.list_tools()
async def list_tools():
    """Expose Bedrock Agents as MCP tools."""
    return [
        Tool(
            name="invoke_customer_agent",
            description="Invoke the customer service Bedrock Agent for support queries",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Customer support question or request"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID for conversation continuity"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="search_knowledge_base",
            description="Search the product knowledge base for information",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Route MCP tool calls to Bedrock services."""

    if name = "invoke_customer_agent":
        response = bedrock_runtime.invoke_agent(
            agentId='AGENT123',
            agentAliasId='ALIAS123',
            sessionId=arguments.get('session_id', 'default'),
            inputText=arguments['query']
        )

        completion = ""
        for event in response['completion']:
            if 'chunk' in event:
                completion += event['chunk']['bytes'].decode('utf-8')

        return [TextContent(type="text", text=completion)]

    elif name = "search_knowledge_base":
        response = bedrock_runtime.retrieve(
            knowledgeBaseId='KB123',
            retrievalQuery={'text': arguments['query']},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': arguments.get('max_results', 5)
                }
            }
        )

        results = [
            {
                'content': r['content']['text'],
                'score': r['score']
            }
            for r in response['retrievalResults']
        ]

        return [TextContent(type="text", text=json.dumps(results))]

    raise ValueError(f"Unknown tool: {name}")