import pandas as pd
import boto3
from itertools import combinations

def intersectional_fairness_analysis(
    data_s3_path,
    predictions_s3_path,
    protected_attributes,
    label_column,
    prediction_column
):
    """
    Analyze fairness across intersections of protected attributes.
    Example: Gender AND Race, not just Gender OR Race separately.
    """
    # Load data (in practice, use SageMaker Processing)
    s3 = boto3.client('s3')

    # Parse S3 paths and load data
    # ... data loading code ...

    # For demonstration, assume data is loaded as DataFrame
    # df = pd.read_csv(...)

    results = {
        'single_attribute': {},
        'intersectional': {}
    }

    # Single attribute analysis
    for attr in protected_attributes:
        groups = df.groupby(attr).agg({
            label_column: 'mean',
            prediction_column: 'mean',
            attr: 'count'
        }).rename(columns={attr: 'count'})

        results['single_attribute'][attr] = {
            'positive_rate_by_group': groups[prediction_column].to_dict(),
            'group_sizes': groups['count'].to_dict()
        }

    # Intersectional analysis (pairs of attributes)
    for attr1, attr2 in combinations(protected_attributes, 2):
        intersection_name = f"{attr1}_x_{attr2}"

        groups = df.groupby([attr1, attr2]).agg({
            label_column: 'mean',
            prediction_column: 'mean',
            attr1: 'count'
        }).rename(columns={attr1: 'count'})

        # Calculate disparate impact for each intersection
        positive_rates = groups[prediction_column]
        max_rate = positive_rates.max()
        min_rate = positive_rates.min()

        intersectional_di = min_rate / max_rate if max_rate > 0 else 0

        results['intersectional'][intersection_name] = {
            'disparate_impact': intersectional_di,
            'max_group': positive_rates.idxmax(),
            'min_group': positive_rates.idxmin(),
            'max_rate': max_rate,
            'min_rate': min_rate,
            'compliant': 0.8 <= intersectional_di <= 1.25
        }

        if not results['intersectional'][intersection_name]['compliant']:
            print(f"WARNING: Intersectional fairness issue found!")
            print(f"  {intersection_name}: DI = {intersectional_di:.3f}")
            print(f"  Advantaged: {positive_rates.idxmax()} (rate: {max_rate:.3f})")
            print(f"  Disadvantaged: {positive_rates.idxmin()} (rate: {min_rate:.3f})")

    return results


def generate_fairness_report(analysis_results):
    """
    Generate comprehensive fairness report.
    """
    report = {
        'summary': {
            'single_attribute_compliant': True,
            'intersectional_compliant': True,
            'overall_compliant': True
        },
        'details': analysis_results,
        'recommendations': []
    }

    # Check single attribute compliance
    for attr, data in analysis_results.get('single_attribute', {}).items():
        rates = list(data['positive_rate_by_group'].values())
        if len(rates) >= 2:
            di = min(rates) / max(rates) if max(rates) > 0 else 0
            if di < 0.8:
                report['summary']['single_attribute_compliant'] = False
                report['recommendations'].append(
                    f"Address {attr} disparity (DI={di:.3f})"
                )

    # Check intersectional compliance
    for intersection, data in analysis_results.get('intersectional', {}).items():
        if not data['compliant']:
            report['summary']['intersectional_compliant'] = False
            report['recommendations'].append(
                f"Address {intersection} intersectional disparity (DI={data['disparate_impact']:.3f})"
            )

    report['summary']['overall_compliant'] = (
        report['summary']['single_attribute_compliant'] and
        report['summary']['intersectional_compliant']
    )

    return report