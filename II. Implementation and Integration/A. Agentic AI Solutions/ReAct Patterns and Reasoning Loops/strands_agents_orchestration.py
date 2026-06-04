from strands import Agent, tool
from strands.models import BedrockModel

# Define tools using Strands decorators
@tool
def search_knowledge_base(query: str) -> str:
    """Search the company knowledge base for relevant information."""
    # Implementation would query Bedrock Knowledge Base
    return f"Found 3 articles matching '{query}'"

@tool
def create_ticket(title: str, description: str, priority: str = "medium") -> str:
    """Create a support ticket in the ticketing system."""
    return f"Created ticket TKT-{12345}: {title}"

@tool
def get_customer_info(customer_id: str) -> str:
    """Retrieve customer information from CRM."""
    return f"Customer {customer_id}: John Doe, Premium tier, Account active"


# Create agent with Bedrock model
model = BedrockModel(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region_name="us-east-1"
)

agent = Agent(
    model=model,
    tools=[search_knowledge_base, create_ticket, get_customer_info],
    system_prompt="""You are a customer support agent. Help customers by:
    1. Looking up their information
    2. Searching for relevant knowledge articles
    3. Creating tickets when needed

    Always gather context before creating tickets."""
)

# Custom orchestration loop with intervention points
def run_with_approval(agent: Agent, query: str, require_approval_for: list = None):
    """Run agent with approval workflow for sensitive actions."""
    require_approval_for = require_approval_for or ["create_ticket"]

    # Start agent reasoning
    response = agent.run(query)

    # Check if any pending actions need approval
    for action in response.pending_actions:
        if action.tool_name in require_approval_for:
            print(f"Approval required for: {action.tool_name}")
            print(f"Parameters: {action.parameters}")
            approval = input("Approve? (y/n): ")

            if approval.lower() = 'y':
                # Execute approved action
                result = agent.execute_tool(action)
                print(f"Action result: {result}")
            else:
                print("Action cancelled by user")

    return response.final_answer


# Run with custom orchestration
result = run_with_approval(
    agent,
    "Customer C-12345 is having login issues. Create a ticket if needed.",
    require_approval_for=["create_ticket"]
)
print(result)