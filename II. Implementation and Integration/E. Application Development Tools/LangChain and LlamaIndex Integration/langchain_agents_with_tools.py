from langchain_aws import ChatBedrock
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
import json

# Initialize model
chat = ChatBedrock(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region_name="us-east-1"
)

# Define custom tools
@tool
def get_weather(location: str) -> str:
    """Get current weather for a location."""
    # Mock implementation
    return json.dumps({
        "location": location,
        "temperature": 72,
        "condition": "sunny"
    })

@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

@tool
def search_documents(query: str) -> str:
    """Search internal documents for information."""
    # Mock implementation - in production, use Bedrock KB
    return f"Found information about: {query}"

# Create agent
def create_assistant_agent():
    """Create an agent with tools."""

    tools = [get_weather, calculate, search_documents]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful assistant with access to tools.
        Use tools when needed to answer questions accurately.
        Always explain your reasoning."""),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])

    agent = create_tool_calling_agent(chat, tools, prompt)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True
    )

    return executor

# RAG with Bedrock Knowledge Base
from langchain_aws import AmazonKnowledgeBasesRetriever
from langchain.chains import RetrievalQA

def create_rag_chain(knowledge_base_id: str):
    """Create RAG chain with Bedrock Knowledge Base."""

    retriever = AmazonKnowledgeBasesRetriever(
        knowledge_base_id=knowledge_base_id,
        retrieval_config={
            "vectorSearchConfiguration": {
                "numberOfResults": 5
            }
        }
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=chat,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )

    return qa_chain

# Usage
agent = create_assistant_agent()
result = agent.invoke({
    "input": "What's the weather in Seattle and what's 25 * 4?"
})
print(result['output'])

# RAG usage
rag = create_rag_chain("KB123456")
answer = rag.invoke({"query": "What is our refund policy?"})
print(answer['result'])