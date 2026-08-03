import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime')

def evaluate_response(question: str, response: str, criteria: str) -> dict:
    """Evaluate a model response using LLM-as-Judge."""

    evaluation_prompt = f"""You are an expert evaluator assessing AI model responses.

TASK: Evaluate the following response based on {criteria}.

SCORING RUBRIC:
5 - Excellent: Fully addresses the question with accurate, complete, and well-structured information
4 - Good: Addresses the question well with minor omissions or improvements possible
3 - Acceptable: Addresses the main points but has notable gaps or issues
2 - Poor: Partially addresses the question with significant problems
1 - Very Poor: Fails to address the question or contains major errors

QUESTION:
{question}

RESPONSE TO EVALUATE:
{response}

INSTRUCTIONS:
1. Analyze the response against the criteria
2. Provide your reasoning in 2-3 sentences
3. Assign a score from 1-5

Return your evaluation in this exact JSON format:
{{"reasoning": "your reasoning here", "score": X}}
"""

    response = bedrock_runtime.converse(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        messages=[{'role': 'user', 'content': [{'text': evaluation_prompt}]}],
        inferenceConfig={
            'maxTokens': 500,
            'temperature': 0.0  # Deterministic for consistency
        }
    )

    result_text = response['output']['message']['content'][0]['text']
    return json.loads(result_text)

# Example usage
question = "What are the benefits of serverless computing?"
model_response = "Serverless computing offers automatic scaling, pay-per-use pricing, and reduced operational overhead."

evaluation = evaluate_response(question, model_response, "helpfulness and completeness")
print(f"Score: {evaluation['score']}/5")
print(f"Reasoning: {evaluation['reasoning']}")