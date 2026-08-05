from fmeval.data_loaders.data_config import DataConfig
from fmeval.model_runners.bedrock_model_runner import BedrockModelRunner
from fmeval.eval_algorithms.factual_knowledge import FactualKnowledge
from fmeval.eval_algorithms.toxicity import Toxicity
import boto3

# Configure Bedrock model runner
model_runner = BedrockModelRunner(
    model_id='anthropic.claude-3-sonnet-20240229-v1:0',
    content_template='{"anthropic_version": "bedrock-2023-05-31", "max_tokens": 512, "messages": [{"role": "user", "content": $prompt}]}',
    output_jmespath='content[0].text'
)

# Configure dataset
data_config = DataConfig(
    dataset_name='my_eval_dataset',
    dataset_uri='s3://my-bucket/eval-data/test_set.jsonl',
    dataset_mime_type='application/jsonlines',
    model_input_location='prompt',
    target_output_location='expected_answer'
)

# Run factual knowledge evaluation
factual_eval = FactualKnowledge()
factual_results = factual_eval.evaluate(
    model=model_runner,
    dataset_configta_config,
    save=True,
    save_path='./eval_results/'
)

print("Factual Knowledge Results:")
for metric in factual_results:
    print(f"  {metric.name}: {metric.value:.3f}")