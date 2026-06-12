from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.agent import ReActAgent
from llama_index.llms.anthropic import Anthropic

# Standard LlamaIndex setup
documents = SimpleDirectoryReader("data/").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()

# Create query tool
query_tool = QueryEngineTool(
    query_engine=query_engine,
    metadata=ToolMetadata(
        name="knowledge_base",
        description="Search the company knowledge base for information"
    )
)

# Create LlamaIndex agent
llm = Anthropic(model="claude-sonnet-4-20250514")
agent = ReActAgent.from_tools(
    [query_tool],
    llm=llm,
    verbose=True
)

# --- Deploy to AgentCore ---
import boto3

agentcore = boto3.client('bedrock-agentcore')

# For LlamaIndex, you can also use AgentCore Memory
# to provide long-term context to the index

response = agentcore.create_runtime_endpoint(
    endpointName='llamaindex-knowledge-agent',
    endpointConfig={
        'agentSource': {
            's3Uri': 's3://my-bucket/agents/llamaindex-kb/'
        },
        'runtime': 'python3.11',
        'memoryMB': 2048,  # More memory for index operations

        'agentCoreConfig': {
            'memoryId': 'knowledge-memory-store',
            # Index tool exposed via Gateway for policy control
            'gatewayId': 'knowledge-gateway'
        }
    }
)