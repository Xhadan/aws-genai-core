from strands import Agent
from strands.tools import tool
from strands.models import BedrockModel
from strands.agentcore import AgentCoreRuntime, AgentCoreMemory, AgentCoreGateway

# Define tools with type hints (Strands feature)
@tool
def get_customer(customer_id: str) -> dict:
    """Get customer details by ID.

    Args:
        customer_id: The unique customer identifier

    Returns:
        Customer details including name, email, and status
    """
    # Implementation
    return {"id": customer_id, "name": "John Doe", "status": "active"}

@tool
def update_customer(customer_id: str, updates: dict) -> dict:
    """Update customer information.

    Args:
        customer_id: The unique customer identifier
        updates: Dictionary of fields to update

    Returns:
        Updated customer details
    """
    # Implementation
    return {"success": True, "updated": updates}

# Create Strands agent
agent = Agent(
    modeldrockModel("anthropic.claude-sonnet-4-20250514"),
    system_prompt="You are a customer service agent. Be helpful and professional.",
    tools=[get_customer, update_customer]
)

# --- Native AgentCore deployment ---
# Strands has built-in AgentCore support

runtime = AgentCoreRuntime(
    name='strands-customer-service',
    memory_mb24,
    timeout_seconds00
)

memory = AgentCoreMemory(
    store_id='customer-memory',
    strategies=['semantic', 'user_preferences']
)

gateway = AgentCoreGateway(
    gateway_id='customer-tools-gateway',
    policy_engine_id='customer-policies'
)

# Deploy with single command
endpoint = runtime.deploy(
    agent,
    memory=memory,
    gateway=gateway,
    tags={'Environment': 'Production'}
)

print(f"Agent deployed: {endpoint.url}")

# Local development still works
# response = agent("What's the status of customer C123?")

# Production invocation through AgentCore
# production_response = endpoint.invoke("What's the status of customer C123?")