# Claude Desktop MCP configuration (claude_desktop_config.json)
# Located at:
# - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
# - Windows: %APPDATA%\Claude\claude_desktop_config.json

config = {
    "mcpServers": {
        "database": {
            "command": "python",
            "args": ["/path/to/database_mcp_server.py"],
            "env": {
                "DATABASE_URL": "postgresql://localhost/mydb"
            }
        },
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/me/projects"]
        },
        "github": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxxx"
            }
        },
        "aws-bedrock": {
            "command": "python",
            "args": ["/path/to/aws_bedrock_mcp_server.py"],
            "env": {
                "AWS_PROFILE": "default",
                "AWS_REGION": "us-east-1"
            }
        }
    }
}

# Example: AWS integration MCP server
# This server could expose Bedrock Knowledge Bases as MCP resources
# and Bedrock Agent invocation as MCP tools