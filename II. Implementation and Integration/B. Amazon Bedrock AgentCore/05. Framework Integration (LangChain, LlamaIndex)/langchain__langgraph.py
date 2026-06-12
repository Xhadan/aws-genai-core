from langchain_core.agents import AgentExecutor
from agentcore.adapters.langchain import AgentCoreAdapter

# Your existing LangChain agent
agent = create_langchain_agent()
executor = AgentExecutor(agent=agent, tools=tools)

# Wrap for AgentCore deployment
adapter = AgentCoreAdapter(executor)
adapter.with_memory('memory-store-id')
adapter.with_gateway('gateway-id')