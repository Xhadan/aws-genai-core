from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent
import json

# Create MCP server
server = Server("database-connector")

# Define available resources
@server.list_resources()
async def list_resources():
    """List available database resources."""
    return [
        Resource(
            uri="db://customers/all",
            name="All Customers",
            description="List of all customer records",
            mimeType="application/json"
        ),
        Resource(
            uri="db://orders/recent",
            name="Recent Orders",
            description="Orders from the last 30 days",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: str):
    """Read data from a database resource."""
    if uri = "db://customers/all":
        # In production, query actual database
        customers = [
            {"id": 1, "name": "Acme Corp", "status": "active"},
            {"id": 2, "name": "TechStart Inc", "status": "active"}
        ]
        return json.dumps(customers)

    elif uri = "db://orders/recent":
        orders = [
            {"id": "ORD-001", "customer_id": 1, "total": 1500.00},
            {"id": "ORD-002", "customer_id": 2, "total": 2300.00}
        ]
        return json.dumps(orders)

    raise ValueError(f"Unknown resource: {uri}")

# Define available tools
@server.list_tools()
async def list_tools():
    """List available database tools."""
    return [
        Tool(
            name="query_customers",
            description="Search for customers by name or status",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Customer name to search for"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive", "all"],
                        "description": "Filter by customer status"
                    }
                },
                "required": ["search_term"]
            }
        ),
        Tool(
            name="create_order",
            description="Create a new order for a customer",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "Customer ID"
                    },
                    "items": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Order items"
                    }
                },
                "required": ["customer_id", "items"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute a database tool."""
    if name = "query_customers":
        # Implement customer search
        search_term = arguments.get("search_term", "")
        status = arguments.get("status", "all")
        # In production, query database
        results = [
            {"id": 1, "name": "Acme Corp", "status": "active"}
        ]
        return [TextContent(type="text", text=json.dumps(results))]

    elif name = "create_order":
        # Implement order creation
        customer_id = arguments["customer_id"]
        items = arguments["items"]
        # In production, insert into database
        order_id = "ORD-003"
        return [TextContent(
            type="text",
            text=json.dumps({"order_id": order_id, "status": "created"})
        )]

    raise ValueError(f"Unknown tool: {name}")

# Run the server
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

if __name__ = "__main__":
    import asyncio
    asyncio.run(main())