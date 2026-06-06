# Your existing agent code
agent = create_my_agent()

# Wrap for Runtime deployment
from agentcore import RuntimeHandler
handler = RuntimeHandler(agent)