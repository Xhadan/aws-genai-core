from llama_index.llms.bedrock import Bedrock
from llama_index.embeddings.bedrock import BedrockEmbedding
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.retrievers import (
    VectorIndexRetriever,
    KeywordTableSimpleRetriever,
    RouterRetriever
)
from llama_index.core.query_engine import (
    RetrieverQueryEngine,
    SubQuestionQueryEngine
)
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.postprocessor import SimilarityPostprocessor

# Configure Bedrock
llm = Bedrock(
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    region_name="us-east-1"
)
Settings.llm = llm
Settings.embed_model = BedrockEmbedding(
    model_name="amazon.titan-embed-text-v2:0"
)

# Hybrid retriever (vector + keyword)
def create_hybrid_retriever(index, keyword_index):
    """Create hybrid retriever combining vector and keyword search."""

    vector_retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=3
    )

    keyword_retriever = KeywordTableSimpleRetriever(
        index=keyword_index,
        max_keywords_per_query=5
    )

    # Router to select best retriever
    router_retriever = RouterRetriever(
        selector=llm,
        retriever_tools=[
            QueryEngineTool(
                query_engine=RetrieverQueryEngine(retriever=vector_retriever),
                metadata=ToolMetadata(
                    name="vector_search",
                    description="Use for semantic similarity search"
                )
            ),
            QueryEngineTool(
                query_engine=RetrieverQueryEngine(retriever=keyword_retriever),
                metadata=ToolMetadata(
                    name="keyword_search",
                    description="Use for exact term matching"
                )
            )
        ]
    )

    return router_retriever

# Sub-question query engine for complex queries
def create_subquestion_engine(indexes: dict):
    """Create engine that breaks complex queries into sub-questions."""

    query_engine_tools = []

    for name, index in indexes.items():
        query_engine = index.as_query_engine()
        tool = QueryEngineTool(
            query_engine=query_engine,
            metadata=ToolMetadata(
                name=name,
                description=f"Provides information about {name}"
            )
        )
        query_engine_tools.append(tool)

    sub_question_engine = SubQuestionQueryEngine.from_defaults(
        query_engine_tools=query_engine_tools,
        llm=llm
    )

    return sub_question_engine

# Custom response synthesis
def create_custom_query_engine(index):
    """Create query engine with custom response synthesis."""

    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=5
    )

    # Post-processor for filtering
    postprocessor = SimilarityPostprocessor(similarity_cutoff=0.7)

    # Custom response synthesizer
    response_synthesizer = get_response_synthesizer(
        response_mode="compact",  # compact, refine, tree_summarize
        llm=llm
    )

    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
        node_postprocessors=[postprocessor]
    )

    return query_engine

# Agentic RAG with tools
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool

def create_rag_agent(index):
    """Create an agent with RAG and custom tools."""

    # Query tool from index
    query_tool = QueryEngineTool(
        query_engine=index.as_query_engine(),
        metadata=ToolMetadata(
            name="knowledge_base",
            description="Search the knowledge base for information"
        )
    )

    # Custom tool
    def calculate(expression: str) -> str:
        """Calculate a math expression."""
        return str(eval(expression))

    calc_tool = FunctionTool.from_defaults(fnlculate)

    # Create agent
    agent = ReActAgent.from_tools(
        tools=[query_tool, calc_tool],
        llm=llm,
        verbose=True
    )

    return agent

# Usage
# agent = create_rag_agent(index)
# response = agent.chat("What is the pricing and calculate 100 * 1.15")