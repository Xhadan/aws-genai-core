from llama_index.llms.bedrock import Bedrock
from llama_index.embeddings.bedrock import BedrockEmbedding
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.memory import ChatMemoryBuffer

# Configure LlamaIndex with Bedrock
def configure_llamaindex():
    """Configure LlamaIndex to use Bedrock."""

    # Set up LLM
    llm = Bedrock(
        model="anthropic.claude-3-sonnet-20240229-v1:0",
        region_name="us-east-1",
        temperature=0.7,
        max_tokens24
    )

    # Set up embeddings
    embed_model = BedrockEmbedding(
        model_name="amazon.titan-embed-text-v2:0",
        region_name="us-east-1"
    )

    # Set as defaults
    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.node_parser = SentenceSplitter(chunk_sizeQ2, chunk_overlapP)

    return llm, embed_model

# Simple query
def simple_query(llm):
    """Simple LLM query."""
    response = llm.complete("What is Amazon Bedrock?")
    return response.text

# Chat with streaming
def stream_chat(llm, message: str):
    """Stream chat response."""
    messages = [{"role": "user", "content": message}]

    for chunk in llm.stream_chat(messages):
        print(chunk.delta, end="", flush=True)

# Build RAG index from documents
def build_document_index(docs_path: str):
    """Build vector index from documents."""

    # Load documents
    documents = SimpleDirectoryReader(docs_path).load_data()
    print(f"Loaded {len(documents)} documents")

    # Create index
    index = VectorStoreIndex.from_documents(
        documents,
        show_progress=True
    )

    return index

# Query engine with custom retrieval
def create_query_engine(index, top_k: int = 5):
    """Create query engine with custom settings."""

    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=top_k
    )

    query_engine = RetrieverQueryEngine(retriever=retriever)

    return query_engine

# Chat engine with memory
def create_chat_engine(index):
    """Create chat engine with conversation memory."""

    memory = ChatMemoryBuffer.from_defaults(token_limit000)

    chat_engine = index.as_chat_engine(
        chat_mode="context",
        memory=memory,
        system_prompt="You are a helpful assistant. Use the provided context to answer questions."
    )

    return chat_engine

# Full RAG application
def run_rag_app():
    """Run a complete RAG application."""

    # Configure
    llm, embed_model = configure_llamaindex()

    # Build index (or load existing)
    index = build_document_index("./documents")

    # Create query engine
    query_engine = create_query_engine(index)

    # Query
    response = query_engine.query("What are the main features?")
    print(f"Answer: {response.response}")
    print(f"Sources: {[n.node.get_content()[:100] for n in response.source_nodes]}")

    # Create chat engine
    chat_engine = create_chat_engine(index)

    # Multi-turn conversation
    response1 = chat_engine.chat("What is this document about?")
    print(f"Response 1: {response1.response}")

    response2 = chat_engine.chat("Can you elaborate on that?")
    print(f"Response 2: {response2.response}")

# Usage
llm, embed_model = configure_llamaindex()
result = simple_query(llm)
print(result)