import boto3
import sagemaker
from sagemaker.clarify import (
    SageMakerClarifyProcessor,
    DataConfig,
    ModelConfig,
    SHAPConfig
)

session = sagemaker.Session()
role = 'arn:aws:iam::123456789012:role/SageMakerRole'

def run_explainability_analysis(
    model_name,
    input_data_s3,
    output_s3,
    baseline_data_s3=None
):
    """
    Run SageMaker Clarify explainability analysis using SHAP.
    """
    clarify_processor = SageMakerClarifyProcessor(
        role=role,
        instance_count=1,
        instance_type='ml.m5.xlarge',
        sagemaker_session=session
    )

    # Data configuration
    data_config = DataConfig(
        s3_data_input_path=input_data_s3,
        s3_output_path=output_s3,
        label='label',  # Target column
        headers=None,   # Auto-detect
        dataset_type='text/csv'
    )

    # Model configuration
    model_config = ModelConfig(
        model_name=model_name,
        instance_count=1,
        instance_type='ml.m5.xlarge',
        accept_type='application/json',
        content_type='text/csv'
    )

    # SHAP configuration for explainability
    shap_config = SHAPConfig(
        baselineseline_data_s3,  # Reference dataset for comparison
        num_samples0,            # Number of synthetic samples
        agg_method='mean_abs',      # Aggregation for global explanations
        save_local_shap_values=True # Save per-instance explanations
    )

    # Run explainability analysis
    clarify_processor.run_explainability(
        data_configta_config,
        model_config=model_config,
        explainability_config=shap_config,
        wait=True
    )

    print(f"Explainability report saved to: {output_s3}")
    return output_s3


def parse_shap_results(bucket, key):
    """
    Parse and visualize SHAP explainability results.
    """
    s3 = boto3.client('s3')
    import json

    response = s3.get_object(Bucket=bucket, Key=key)
    results = json.loads(response['Body'].read().decode())

    # Extract global feature importance
    global_shap = results.get('explanations', {}).get('kernel_shap', {})

    print("== Global Feature Importance ==")
    for feature, importance in sorted(
        global_shap.get('global_shap_values', {}).items(),
        key=lambda x: abs(x[1]),
        reverse=True
    ):
        direction = "+" if importance > 0 else "-"
        print(f"  {feature}: {direction}{abs(importance):.4f}")

    return results


# Example usage
run_explainability_analysis(
    model_name='my-deployed-model',
    input_data_s3='s3://my-bucket/data/test-samples.csv',
    output_s3='s3://my-bucket/clarify-output/explainability/',
    baseline_data_s3='s3://my-bucket/data/baseline.csv'
)