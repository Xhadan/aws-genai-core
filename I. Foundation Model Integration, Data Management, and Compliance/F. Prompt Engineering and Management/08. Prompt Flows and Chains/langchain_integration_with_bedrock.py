from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from pydantic import BaseModel, Field
from typing import List

# Initialize Bedrock model
model = ChatBedrock(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    model_kwargs={"temperature": 0.7, "max_tokens": 2048}
)

# Simple Sequential Chain
def create_simple_chain():
    """Create a simple sequential chain."""

    # Step 1: Summarize
    summarize_prompt = ChatPromptTemplate.from_template(
        "Summarize the following text in 2-3 sentences:\n\n{text}"
    )

    # Step 2: Extract key points
    extract_prompt = ChatPromptTemplate.from_template(
        "Extract 3 key points from this summary:\n\n{summary}"
    )

    # Chain them together using LCEL
    chain = (
        {"text": RunnablePassthrough()}
        | summarize_prompt
        | model
        | StrOutputParser()
        | (lambda x: {"summary": x})
        | extract_prompt
        | model
        | StrOutputParser()
    )

    return chain


# Parallel Chain
def create_parallel_chain():
    """Create a chain that processes in parallel."""

    sentiment_prompt = ChatPromptTemplate.from_template(
        "Analyze the sentiment of this text (positive/negative/neutral):\n{text}"
    )

    topics_prompt = ChatPromptTemplate.from_template(
        "Extract the main topics from this text as a comma-separated list:\n{text}"
    )

    entities_prompt = ChatPromptTemplate.from_template(
        "Extract named entities (people, organizations, locations) from:\n{text}"
    )

    # Parallel execution
    chain = RunnablePassthrough() | {
        "sentiment": sentiment_prompt | model | StrOutputParser(),
        "topics": topics_prompt | model | StrOutputParser(),
        "entities": entities_prompt | model | StrOutputParser(),
        "original": RunnablePassthrough()
    }

    return chain


# Conditional Chain
def create_conditional_chain():
    """Create a chain with conditional routing."""

    # Classifier
    classify_prompt = ChatPromptTemplate.from_template(
        """Classify this query into exactly one category:
        - technical: Technical questions or issues
        - billing: Billing, pricing, payment questions
        - general: General inquiries

        Query: {query}
        Category:"""
    )

    # Specialized handlers
    technical_prompt = ChatPromptTemplate.from_template(
        "Provide a technical solution for: {query}"
    )

    billing_prompt = ChatPromptTemplate.from_template(
        "Address this billing inquiry: {query}"
    )

    general_prompt = ChatPromptTemplate.from_template(
        "Provide helpful information for: {query}"
    )

    def route(info):
        category = info["category"].strip().lower()
        query = info["query"]

        if "technical" in category:
            return technical_prompt.format(query=query)
        elif "billing" in category:
            return billing_prompt.format(query=query)
        else:
            return general_prompt.format(query=query)

    chain = (
        {"query": RunnablePassthrough()}
        | RunnablePassthrough.assign(
            category=classify_prompt | model | StrOutputParser()
        )
        | RunnableLambda(route)
        | model
        | StrOutputParser()
    )

    return chain


# Structured Output Chain
class AnalysisResult(BaseModel):
    summary: str = Field(description="Brief summary")
    sentiment: str = Field(description="Overall sentiment")
    key_points: List[str] = Field(description="Key points")
    confidence: float = Field(description="Confidence score 0-1")

def create_structured_chain():
    """Create a chain that outputs structured data."""

    prompt = ChatPromptTemplate.from_template(
        """Analyze this text and provide structured output.

        Text: {text}

        Respond with a JSON object containing:
        - summary: Brief summary
        - sentiment: positive, negative, or neutral
        - key_points: Array of 3 key points
        - confidence: Your confidence score from 0 to 1

        JSON:"""
    )

    chain = prompt | model | JsonOutputParser()

    return chain


# Example usage
simple = create_simple_chain()
parallel = create_parallel_chain()
conditional = create_conditional_chain()
structured = create_structured_chain()

# Run examples
text = "AWS Lambda announced new pricing tiers that reduce costs by 20% for high-volume users."

print("Simple chain:", simple.invoke(text))
print("Parallel chain:", parallel.invoke({"text": text}))
print("Conditional chain:", conditional.invoke("How do I fix Lambda timeout errors?"))
print("Structured chain:", structured.invoke({"text": text}))