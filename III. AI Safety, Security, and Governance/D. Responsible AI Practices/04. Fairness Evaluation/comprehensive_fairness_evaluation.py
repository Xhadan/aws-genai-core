import boto3
import sagemaker
from sagemaker.clarify import (
    SageMakerClarifyProcessor,
    DataConfig,
    BiasConfig,
    ModelConfig,
    ModelPredictedLabelConfig
)
import json

session = sagemaker.Session()
role = 'arn:aws:iam::123456789012:role/SageMakerRole'

def comprehensive_fairness_evaluation(
    model_name,
    input_data_s3,
    output_s3,
    label_column,
    protected_attributes,
    positive_label_value=1
):
    """
    Run comprehensive fairness evaluation across multiple protected attributes.
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
        label=label_column,
        headers=None,
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

    # Predicted label configuration
    predictions_config = ModelPredictedLabelConfig(
        probability_threshold=0.5
    )

    results = {}

    # Evaluate each protected attribute
    for attr_name, attr_config in protected_attributes.items():
        print(f"\nEvaluating fairness for: {attr_name}")

        bias_config = BiasConfig(
            label_values_or_threshold=[positive_label_value],
            facet_name=attr_name,
            facet_values_or_threshold=attr_config['facet_values'],
            group_name=attr_config.get('group_name')  # For conditional analysis
        )

        # Output path for this attribute
        attr_output = f"{output_s3}/{attr_name}/"

        attr_data_config = DataConfig(
            s3_data_input_path=input_data_s3,
            s3_output_path=attr_output,
            label=label_column,
            headers=None,
            dataset_type='text/csv'
        )

        # Run both pre-training and post-training bias
        clarify_processor.run_bias(
            data_config=attr_data_config,
            bias_config=bias_config,
            model_config=model_config,
            model_predicted_label_config=predictions_config,
            pre_training_methods='all',
            post_training_methods='all',
            wait=True
        )

        results[attr_name] = attr_output

    return results


def analyze_fairness_report(bucket, key):
    """
    Analyze Clarify fairness report and identify issues.
    """
    s3 = boto3.client('s3')

    response = s3.get_object(Bucket=bucket, Key=key)
    report = json.loads(response['Body'].read().decode())

    analysis = {
        'attribute': report.get('facet', 'Unknown'),
        'pre_training_issues': [],
        'post_training_issues': [],
        'recommendations': [],
        'compliant': True
    }

    # Define thresholds
    thresholds = {
        'CI': 0.1,      # Class Imbalance
        'DPL': 0.1,     # Difference in Positive Labels
        'DPPL': 0.1,    # Difference in Predicted Positive Labels (Demographic Parity)
        'DI_low': 0.8,  # Disparate Impact lower bound (80% rule)
        'DI_high': 1.25, # Disparate Impact upper bound
        'AD': 0.05,     # Accuracy Difference
        'TE': 0.05      # Treatment Equality
    }

    # Check pre-training metrics
    for metric in report.get('pre_training_bias_metrics', []):
        name = metric['name']
        value = metric['value']

        if name = 'CI' and abs(value) > thresholds['CI']:
            analysis['pre_training_issues'].append({
                'metric': 'Class Imbalance',
                'value': value,
                'threshold': thresholds['CI'],
                'severity': 'HIGH' if abs(value) > 0.3 else 'MEDIUM'
            })
            analysis['recommendations'].append(
                f"Address class imbalance (CI={value:.3f}): Consider resampling, "
                "SMOTE, or collecting more data for underrepresented groups"
            )
            analysis['compliant'] = False

        if name = 'DPL' and abs(value) > thresholds['DPL']:
            analysis['pre_training_issues'].append({
                'metric': 'Difference in Positive Labels',
                'value': value,
                'threshold': thresholds['DPL'],
                'severity': 'HIGH' if abs(value) > 0.2 else 'MEDIUM'
            })
            analysis['recommendations'].append(
                f"Label distribution imbalance (DPL={value:.3f}): Review labeling "
                "process for potential bias"
            )
            analysis['compliant'] = False

    # Check post-training metrics
    for metric in report.get('post_training_bias_metrics', []):
        name = metric['name']
        value = metric['value']

        if name = 'DPPL' and abs(value) > thresholds['DPPL']:
            analysis['post_training_issues'].append({
                'metric': 'Demographic Parity',
                'value': value,
                'threshold': thresholds['DPPL'],
                'severity': 'HIGH' if abs(value) > 0.2 else 'MEDIUM'
            })
            analysis['recommendations'].append(
                f"Demographic parity violation (DPPL={value:.3f}): Consider "
                "threshold adjustment or model debiasing"
            )
            analysis['compliant'] = False

        if name = 'DI':
            if value < thresholds['DI_low'] or value > thresholds['DI_high']:
                analysis['post_training_issues'].append({
                    'metric': 'Disparate Impact',
                    'value': value,
                    'threshold': f"{thresholds['DI_low']}-{thresholds['DI_high']}",
                    'severity': 'HIGH'  # Legal compliance
                })
                analysis['recommendations'].append(
                    f"Disparate Impact violation (DI={value:.3f}): Model may violate "
                    "80% rule. Consider adversarial debiasing or reject option classification"
                )
                analysis['compliant'] = False

        if name = 'AD' and abs(value) > thresholds['AD']:
            analysis['post_training_issues'].append({
                'metric': 'Accuracy Difference',
                'value': value,
                'threshold': thresholds['AD'],
                'severity': 'MEDIUM'
            })
            analysis['recommendations'].append(
                f"Accuracy varies by group (AD={value:.3f}): Model performs "
                "differently across groups. Review feature engineering."
            )

    return analysis


# Example: Evaluate loan approval model
protected_attrs = {
    'gender': {
        'facet_values': [0],  # 0 = female (disadvantaged group)
        'group_name': None
    },
    'age': {
        'facet_values': [40],  # Threshold: under 40
        'group_name': None
    },
    'race': {
        'facet_values': [1, 2, 3],  # Non-majority groups
        'group_name': None
    }
}

results = comprehensive_fairness_evaluation(
    model_name='loan-approval-model',
    input_data_s3='s3://my-bucket/data/loan-applications.csv',
    output_s3='s3://my-bucket/fairness-evaluation/',
    label_column='approved',
    protected_attributes=protected_attrs
)

# Analyze results for each attribute
for attr, output_path in results.items():
    analysis = analyze_fairness_report('my-bucket', f'fairness-evaluation/{attr}/analysis.json')
    print(f"\n== {attr.upper()} Fairness Analysis ==")
    print(f"Compliant: {analysis['compliant']}")
    if not analysis['compliant']:
        for rec in analysis['recommendations']:
            print(f"  - {rec}")