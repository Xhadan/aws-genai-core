from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

# Initialize Bedrock chat model
chat = ChatBedrock(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region_name="us-east-1",
    model_kwargs={
        "max_tokens": 1024,
        "temperature": 0.7
    }
)

# Simple invocation
def simple_chat(message: str) -> str:
    """Simple chat invocation."""
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content=message)
    ]
    response = chat.invoke(messages)
    return response.content

# Streaming response
def stream_chat(message: str):
    """Stream chat response."""
    messages = [HumanMessage(content=message)]
    for chunk in chat.stream(messages):
        print(chunk.content, end="", flush=True)

# Chain with prompt template
def create_summarization_chain():
    """Create a summarization chain."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert at summarizing documents."),
        ("human", "Summarize the following text in {num_points} bullet points:\n\n{text}")
    ])

    chain = prompt | chat | StrOutputParser()
    return chain

# Conversation with memory
def create_conversation_chain():
    """Create a conversation chain with memory."""
    memory = ConversationBufferMemory(return_messages=True)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI assistant."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

    chain = ConversationChain(
        llm=chat,
        memory=memory,
        prompt=prompt
    )

    return chain

# Embeddings
def get_embeddings():
    """Get Bedrock embeddings."""
    embeddings = BedrockEmbeddings(
        model_id="amazon.titan-embed-text-v2:0",
        region_name="us-east-1"
    )

    # Embed single text
    vector = embeddings.embed_query("What is cloud computing?")
    print(f"Embedding dimension: {len(vector)}")

    # Embed multiple texts
    vectors = embeddings.embed_documents([
        "First document about AWS.",
        "Second document about Azure.",
        "Third document about GCP."
    ])
    print(f"Embedded {len(vectors)} documents")

    return embeddings

# Usage
result = simple_chat("What is Amazon Bedrock?")
print(result)

summarizer = create_summarization_chain()
summary = summarizer.invoke({
    "text": "Long document text here...",
    "num_points": "3"
})
print(summary)