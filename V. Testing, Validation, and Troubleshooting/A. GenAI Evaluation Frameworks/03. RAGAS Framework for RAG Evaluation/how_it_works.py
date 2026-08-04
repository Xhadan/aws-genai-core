import boto3
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from datasets import Dataset
from langchain_aws import BedrockEmbeddings, ChatBedrock

# Configure Bedrock models for RAGAS
bedrock_runtime = boto3.client('bedrock-runtime')

# LLM for evaluation (judge)
llm = ChatBedrock(
    model_id='anthropic.claude-3-5-sonnet-20241022-v2:0',
    clientdrock_runtime
)

# Embeddings for similarity calculations
embeddings = BedrockEmbeddings(
    model_id='amazon.titan-embed-text-v2:0',
    clientdrock_runtime
)

# Prepare evaluation dataset
# Each sample needs: question, answer, contexts, ground_truth (optional)
eval_data = {
    'question': [
        'What is Amazon Bedrock?',
        'How does RAG work?'
    ],
    'answer': [
        'Amazon Bedrock is a fully managed service that offers foundation models from leading AI providers through a single API.',
        'RAG retrieves relevant documents and uses them as context when generating responses.'
    ],
    'contexts': [
        ['Amazon Bedrock is a fully managed service that offers a choice of high-performing foundation models from leading AI companies.'],
        ['Retrieval Augmented Generation (RAG) combines retrieval and generation to produce grounded responses.']
    ],
    'ground_truth': [
        'Amazon Bedrock is a managed service providing access to foundation models via API.',
        'RAG retrieves documents and includes them in the prompt for the LLM to generate grounded answers.'
    ]
}

dataset = Dataset.from_dict(eval_data)

# Run RAGAS evaluation
results = evaluate(
    dataset,
    metrics=[
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall
    ],
    llm=llm,
    embeddings=embeddings
)

# Display results
print("RAGAS Evaluation Results:")
print(f"  Faithfulness: {results['faithfulness']:.3f}")
print(f"  Answer Relevancy: {results['answer_relevancy']:.3f}")
print(f"  Context Precision: {results['context_precision']:.3f}")
print(f"  Context Recall: {results['context_recall']:.3f}")