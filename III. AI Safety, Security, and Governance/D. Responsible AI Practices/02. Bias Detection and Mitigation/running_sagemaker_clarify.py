import boto3
import sagemaker
from sagemaker.clarify import SageMakerClarifyProcessor, DataConfig, BiasConfig

session = sagemaker.Session()
role = 'arn:aws:iam::123456789012:role/SageMakerRole'

def run_bias_analysis(
    input_data_s3,
    output_s3,
    label_column,
    facet_column,
    facet_values_or_threshold
):
    """
    Run SageMaker Clarify bias detection.
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
        label='label',
        headers=None,  # Auto-detect from CSV
        dataset_type='text/csv'
    )

    # Bias configuration
    bias_config = BiasConfig(
        label_values_or_threshold=[1],  # Positive outcome
        facet_namecet_column,  # Protected attribute (e.g., 'gender')
        facet_values_or_thresholdcet_values_or_threshold,  # e.g., [0] for one group
        group_name=None  # Optional: subgroup for conditional analysis
    )

    # Run pre-training bias analysis
    clarify_processor.run_pre_training_bias(
        data_configta_config,
        data_bias_config=bias_config,
        wait=True
    )

    print(f"Bias report saved to: {output_s3}")
    return output_s3

# Example: Analyze loan application data for gender bias
run_bias_analysis(
    input_data_s3='s3://my-bucket/training-data/loans.csv',
    output_s3='s3://my-bucket/clarify-output/',
    label_column='approved',
    facet_column='gender',
    facet_values_or_threshold=[0]  # 0 = female in this example
)