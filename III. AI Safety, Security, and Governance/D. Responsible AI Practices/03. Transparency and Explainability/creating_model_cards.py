import boto3
import json
from datetime import datetime

sagemaker = boto3.client('sagemaker')

def create_model_card(
    model_name,
    model_description,
    intended_uses,
    training_details,
    evaluation_results,
    ethical_considerations
):
    """
    Create a SageMaker Model Card for transparency documentation.
    """
    model_card_name = f"{model_name}-card"

    # Model Card content structure
    content = {
        "model_overview": {
            "model_name": model_name,
            "model_description": model_description,
            "model_version": "1.0",
            "model_owner": "ML Team",
            "problem_type": "Text Generation"
        },
        "intended_uses": {
            "intended_uses": intended_uses.get('approved_uses', []),
            "factors_affecting_model_efficiency": intended_uses.get('factors', []),
            "risk_rating": intended_uses.get('risk_rating', 'Medium'),
            "explanations_for_risk_rating": intended_uses.get('risk_explanation', '')
        },
        "training_details": {
            "objective_function": training_details.get('objective', ''),
            "training_observations": training_details.get('observations', []),
            "training_job_details": {
                "training_arn": training_details.get('training_arn', ''),
                "training_datasets": training_details.get('datasets', []),
                "training_environment": {
                    "container_image": training_details.get('container', [])
                },
                "training_metrics": training_details.get('metrics', [])
            }
        },
        "evaluation_details": [
            {
                "name": "Primary Evaluation",
                "evaluation_observation": evaluation_results.get('observation', ''),
                "evaluation_job_arn": evaluation_results.get('job_arn', ''),
                "datasets": evaluation_results.get('datasets', []),
                "metric_groups": evaluation_results.get('metric_groups', [])
            }
        ],
        "additional_information": {
            "ethical_considerations": ethical_considerations.get('considerations', ''),
            "caveats_and_recommendations": ethical_considerations.get('caveats', ''),
            "custom_details": ethical_considerations.get('custom', {})
        }
    }

    response = sagemaker.create_model_card(
        ModelCardName=model_card_name,
        Content=json.dumps(content),
        ModelCardStatus='Draft',  # Draft, PendingReview, Approved, Archived
        SecurityConfig={
            'KmsKeyId': 'alias/sagemaker-key'  # Optional encryption
        }
    )

    print(f"Model Card created: {response['ModelCardArn']}")
    return response['ModelCardArn']


def update_model_card_status(model_card_name, new_status):
    """
    Update Model Card status through approval workflow.
    """
    # Get current content
    current = sagemaker.describe_model_card(ModelCardName=model_card_name)

    response = sagemaker.update_model_card(
        ModelCardName=model_card_name,
        Content=current['Content'],
        ModelCardStatus=new_status  # PendingReview, Approved, Archived
    )

    print(f"Model Card status updated to: {new_status}")
    return response


def export_model_card(model_card_name, s3_output):
    """
    Export Model Card as PDF for sharing.
    """
    response = sagemaker.create_model_card_export_job(
        ModelCardName=model_card_name,
        ModelCardVersion=0,  # Latest version
        OutputConfig={
            'S3OutputPath': s3_output
        },
        ModelCardExportJobName=f"{model_card_name}-export-{int(datetime.now().timestamp())}"
    )

    print(f"Export job started: {response['ModelCardExportJobArn']}")
    return response['ModelCardExportJobArn']


# Example: Create Model Card for a GenAI application
model_card_arn = create_model_card(
    model_name="customer-support-assistant",
    model_description="GenAI-powered customer support chatbot using Claude on Bedrock",
    intended_uses={
        'approved_uses': [
            "Answer customer questions about products",
            "Provide order status updates",
            "Route complex issues to human agents"
        ],
        'factors': [
            "Performance may vary for technical product questions",
            "Not designed for medical or legal advice"
        ],
        'risk_rating': 'Medium',
        'risk_explanation': 'Customer-facing with potential for incorrect information'
    },
    training_details={
        'objective': 'Provide accurate, helpful customer support responses',
        'observations': ['Fine-tuned on historical support tickets'],
        'datasets': ['s3://my-bucket/training-data/support-tickets/'],
        'metrics': [{'Name': 'Accuracy', 'Value': 0.92}]
    },
    evaluation_results={
        'observation': 'Model performs well on standard queries, struggles with edge cases',
        'datasets': ['s3://my-bucket/eval-data/test-set/'],
        'metric_groups': [
            {
                'name': 'Quality Metrics',
                'metric_data': [
                    {'name': 'Relevance', 'value': 0.89},
                    {'name': 'Helpfulness', 'value': 0.91}
                ]
            }
        ]
    },
    ethical_considerations={
        'considerations': 'Model may reflect biases in training data. Human review for escalated cases.',
        'caveats': 'Not suitable for medical, legal, or financial advice. Always disclose AI nature.',
        'custom': {'last_bias_review': '2024-01-15'}
    }
)