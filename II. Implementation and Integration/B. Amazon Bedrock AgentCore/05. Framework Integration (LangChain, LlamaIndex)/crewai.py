from crewai import Crew, Agent, Task
from agentcore.adapters.crewai import AgentCoreAdapter

# Your existing CrewAI crew
crew = Crew(
    agents=[researcher, writer, reviewer],
    tasks=[research_task, write_task, review_task]
)

# Deploy to AgentCore
adapter = AgentCoreAdapter(crew)
adapter.with_runtime_config(timeout_hours=4)
adapter.with_shared_memory('team-memory-store')