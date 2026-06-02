from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio

async def use_mcp_server():
    """Connect to and use an MCP server."""

    # Define server connection parameters
    server_params = StdioServerParameters(
        command="python",
        args=["database_mcp_server.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            # List available resources
            resources = await session.list_resources()
            print("\nAvailable resources:")
            for resource in resources.resources:
                print(f"  - {resource.uri}: {resource.description}")

            # Read a resource
            customer_data = await session.read_resource("db://customers/all")
            print(f"\nCustomers: {customer_data.contents[0].text}")

            # Call a tool
            result = await session.call_tool(
                "query_customers",
                {"search_term": "Acme", "status": "active"}
            )
            print(f"\nSearch results: {result.content[0].text}")

# Run the client
asyncio.run(use_mcp_server())