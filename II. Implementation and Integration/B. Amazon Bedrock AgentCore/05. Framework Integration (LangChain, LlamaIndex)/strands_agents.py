from strands import Agent
from strands.tools import tool
from strands.agentcore import deploy

@tool
def search_customers(query: str) -> str:
    """Search customer database."""
    return results

agent = Agent(
    model="anthropic.claude-sonnet-4-20250514",
    tools=[search_customers]
)

# Native deployment to AgentCore
endpoint = deploy(
    agent,
    name='customer-agent',
    memory_store='memory-id',
    gateway='gateway-id'
)