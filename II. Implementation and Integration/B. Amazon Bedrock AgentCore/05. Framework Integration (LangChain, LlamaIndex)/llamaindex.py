from llama_index.core.agent import ReActAgent
from agentcore.adapters.llamaindex import AgentCoreAdapter

# Your existing LlamaIndex agent
agent = ReActAgent.from_tools(tools, llm=llm)

# Wrap for AgentCore
adapter = AgentCoreAdapter(agent)
adapter.with_memory('memory-store-id')