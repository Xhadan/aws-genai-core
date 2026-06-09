from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool

# Define CrewAI agents with roles
researcher = Agent(
    role="Market Researcher",
    goal="Research market trends and competitor analysis",
    backstory="Expert market analyst with 10 years experience",
    tools=[SerperDevTool()],
    verbose=True
)

analyst = Agent(
    role="Data Analyst",
    goal="Analyze research findings and identify patterns",
    backstory="Statistical expert who turns data into insights"
)

writer = Agent(
    role="Report Writer",
    goal="Create comprehensive market reports",
    backstory="Technical writer specializing in business reports"
)

# Define tasks
research_task = Task(
    description="Research the AI agent market trends for 2025",
    agent=researcher,
    expected_output="Market research findings"
)

analysis_task = Task(
    description="Analyze the research and identify key trends",
    agent=analyst,
    expected_output="Trend analysis report"
)

writing_task = Task(
    description="Write a comprehensive market report",
    agent=writer,
    expected_output="Final market report"
)

# Create crew
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analysis_task, writing_task],
    process=Process.sequential  # or Process.hierarchical
)

# --- Deploy to AgentCore ---
import boto3

agentcore = boto3.client('bedrock-agentcore')

response = agentcore.create_runtime_endpoint(
    endpointName='crewai-market-research',
    endpointConfig={
        'agentSource': {
            's3Uri': 's3://my-bucket/agents/crewai-research/'
        },
        'runtime': 'python3.11',
        'memoryMB': 4096,  # Multi-agent needs more memory
        'timeoutSeconds': 14400,  # 4 hours for complex research

        'agentCoreConfig': {
            # Shared memory for crew collaboration
            'memoryId': 'research-shared-memory',
            # Tools routed through Gateway
            'gatewayId': 'research-tools-gateway',
            'observabilityEnabled': True
        }
    }
)

# Multi-agent execution with:
# - Shared memory for agent coordination
# - Gateway policy on external tool access
# - Full trace of agent interactions