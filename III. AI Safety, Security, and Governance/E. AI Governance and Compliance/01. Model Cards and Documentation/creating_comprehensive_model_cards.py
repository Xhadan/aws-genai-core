import boto3
import json
from datetime import datetime

sagemaker = boto3.client('sagemaker')

def create_production_model_card(
    model_name,
    model_description,
    model_arn,
    training_job_arn,
    evaluation_results,
    bias_results=None
):
    """
    Create a comprehensive Model Card for production deployment.
    """
    model_card_name = f"{model_name}-card"

    # Build comprehensive content
    content = {
        "model_overview": {
            "model_name": model_name,
            "model_description": model_description,
            "model_version": "1.0.0",
            "model_owner": "ML Platform Team",
            "model_artifact": [model_arn],
            "problem_type": "Text Generation",
            "algorithm_type": "Large Language Model",
            "model_creator": "GenAI Team",
            "inference_environment": {
                "container_image": ["bedrock-runtime"]
            }
        },
        "intended_uses": {
            "intended_uses": [
                "Customer support chatbot responses",
                "FAQ answer generation",
                "Product description summarization"
            ],
            "factors_affecting_model_efficiency": [
                "Performance degrades on technical jargon not in training data",
                "May struggle with multi-turn conversations exceeding 10 turns",
                "Response quality varies with input length (optimal: 50-500 tokens)"
            ],
            "risk_rating": "Medium",
            "explanations_for_risk_rating": (
                "Customer-facing application with potential for incorrect or "
                "inappropriate responses. Mitigated by Bedrock Guardrails and "
                "human escalation paths."
            )
        },
        "training_details": {
            "objective_function": {
                "function": "Cross-entropy loss for next token prediction",
                "notes": "Fine-tuned on domain-specific customer support data"
            },
            "training_observations": [
                "Model converged after 3 epochs",
                "No signs of overfitting observed",
                "Validation loss stabilized at 0.82"
            ],
            "training_job_details": {
                "training_arn": training_job_arn,
                "training_datasets": [
                    {
                        "name": "Customer Support Conversations",
                        "url": "s3://my-bucket/training-data/support-v2/",
                        "notes": "50,000 curated support conversations"
                    },
                    {
                        "name": "Product Documentation",
                        "url": "s3://my-bucket/training-data/product-docs/",
                        "notes": "Company product documentation corpus"
                    }
                ],
                "training_environment": {
                    "container_image": ["sagemaker-training:latest"]
                },
                "training_metrics": [
                    {"name": "TrainingLoss", "value": 0.78},
                    {"name": "ValidationLoss", "value": 0.82},
                    {"name": "Perplexity", "value": 12.4}
                ],
                "user_provided_training_metrics": [
                    {"name": "BLEU", "value": 0.67},
                    {"name": "ROUGE-L", "value": 0.71}
                ]
            }
        },
        "evaluation_details": [
            {
                "name": "Quality Evaluation",
                "evaluation_observation": (
                    "Model performs well on standard support queries. "
                    "Struggles with edge cases involving recent product updates."
                ),
                "evaluation_job_arn": evaluation_results.get('job_arn', ''),
                "datasets": [
                    {
                        "name": "Test Set",
                        "url": "s3://my-bucket/eval-data/test-set/",
                        "notes": "5,000 held-out support conversations"
                    }
                ],
                "metadata": {
                    "evaluation_date": str(datetime.utcnow().date()),
                    "evaluator": "ML Platform Team"
                },
                "metric_groups": [
                    {
                        "name": "Quality Metrics",
                        "metric_data": [
                            {"name": "Relevance", "value": 0.89, "type": "number"},
                            {"name": "Helpfulness", "value": 0.87, "type": "number"},
                            {"name": "Accuracy", "value": 0.91, "type": "number"}
                        ]
                    },
                    {
                        "name": "Safety Metrics",
                        "metric_data": [
                            {"name": "Toxicity Rate", "value": 0.001, "type": "number"},
                            {"name": "PII Leak Rate", "value": 0.0, "type": "number"}
                        ]
                    }
                ]
            }
        ],
        "additional_information": {
            "ethical_considerations": (
                "Model was tested for demographic bias using SageMaker Clarify. "
                "No significant disparities found in response quality across user groups. "
                "Guardrails configured to prevent harmful outputs and PII exposure."
            ),
            "caveats_and_recommendations": (
                "1. Not suitable for medical, legal, or financial advice. "
                "2. Should not be used for high-stakes decisions without human review. "
                "3. Monitor for drift and retrain quarterly. "
                "4. Always disclose AI nature to end users."
            ),
            "custom_details": {
                "guardrail_id": "guardrail-abc123",
                "last_bias_review": str(datetime.utcnow().date()),
                "data_retention_policy": "90 days",
                "pii_handling": "Masked at inference via Guardrails",
                "human_oversight": "Escalation to agents for low-confidence responses"
            }
        }
    }

    # Add bias results if available
    if bias_results:
        content['evaluation_details'].append({
            "name": "Fairness Evaluation",
            "evaluation_observation": bias_results.get('summary', ''),
            "datasets": bias_results.get('datasets', []),
            "metric_groups": [
                {
                    "name": "Bias Metrics",
                    "metric_data": bias_results.get('metrics', [])
                }
            ]
        })

    response = sagemaker.create_model_card(
        ModelCardName=model_card_name,
        Content=json.dumps(content),
        ModelCardStatus='Draft',
        SecurityConfig={
            'KmsKeyId': 'alias/sagemaker-key'
        },
        Tags=[
            {'Key': 'Project', 'Value': 'CustomerSupport'},
            {'Key': 'Environment', 'Value': 'Production'}
        ]
    )

    print(f"Model Card created: {response['ModelCardArn']}")
    return response['ModelCardArn']


def link_model_card_to_registry(model_card_name, model_package_group_name, model_package_arn):
    """
    Associate Model Card with Model Registry for versioned tracking.
    """
    # Update model package with Model Card reference
    sagemaker.update_model_package(
        ModelPackageArn=model_package_arn,
        CustomerMetadataProperties={
            'ModelCardName': model_card_name,
            'ModelCardArn': f"arn:aws:sagemaker:us-east-1:123456789012:model-card/{model_card_name}"
        }
    )

    print(f"Model Card linked to Model Package: {model_package_arn}")


# Example usage
model_card_arn = create_production_model_card(
    model_name="customer-support-genai-v1",
    model_description="Fine-tuned LLM for customer support response generation",
    model_arn="arn:aws:sagemaker:us-east-1:123456789012:model/support-model-v1",
    training_job_arn="arn:aws:sagemaker:us-east-1:123456789012:training-job/support-training-123",
    evaluation_results={
        'job_arn': 'arn:aws:sagemaker:us-east-1:123456789012:processing-job/eval-123',
        'summary': 'Model meets quality thresholds'
    },
    bias_results={
        'summary': 'No significant bias detected across demographic groups',
        'metrics': [
            {'name': 'Disparate Impact', 'value': 0.95, 'type': 'number'},
            {'name': 'Demographic Parity', 'value': 0.02, 'type': 'number'}
        ]
    }
)