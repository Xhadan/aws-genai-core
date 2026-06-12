from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

# Standard LangChain agent definition
@tool
def search_orders(customer_id: str) -> str:
    """Search orders for a customer."""
    # Implementation
    return f"Orders for {customer_id}: [...]"

@tool
def process_refund(order_id: str, amount: float) -> str:
    """Process a refund for an order."""
    # Implementation
    return f"Refund of ${amount} processed for {order_id}"

# Create LangChain agent
llm = ChatAnthropic(model="claude-sonnet-4-20250514")
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a customer service agent."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

agent = create_tool_calling_agent(llm, [search_orders, process_refund], prompt)
executor = AgentExecutor(agent=agent, tools=[search_orders, process_refund])

# --- Deploy to AgentCore ---
import boto3

agentcore = boto3.client('bedrock-agentcore')

# Package agent code
# (In practice, package to S3)

# Create Runtime endpoint
response = agentcore.create_runtime_endpoint(
    endpointName='langchain-customer-service',
    endpointConfig={
        'agentSource': {
            's3Uri': 's3://my-bucket/agents/langchain-cs/'
        },
        'runtime': 'python3.11',
        'memoryMB': 1024,

        # AgentCore integrations
        'agentCoreConfig': {
            'memoryId': 'customer-memory-store',
            'gatewayId': 'enterprise-gateway',
            'observabilityEnabled': True
        }
    }
)

# Agent now runs with AgentCore infrastructure:
# - Serverless scaling via Runtime
# - Tools routed through Gateway with policy enforcement
# - Memory persists across sessions
# - Full observability and tracing