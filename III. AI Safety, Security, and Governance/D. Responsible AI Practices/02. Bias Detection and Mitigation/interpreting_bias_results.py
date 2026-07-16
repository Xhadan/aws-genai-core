import json
import boto3

s3 = boto3.client('s3')

def analyze_bias_report(bucket, key):
    """
    Parse Clarify bias report and identify issues.
    """
    response = s3.get_object(Bucket=bucket, Key=key)
    report = json.loads(response['Body'].read().decode())

    issues = []
    recommendations = []

    for metric in report.get('pre_training_bias_metrics', []):
        metric_name = metric['name']
        value = metric['value']

        # Check against thresholds
        if metric_name = 'CI' and abs(value) > 0.1:
            issues.append(f"Class Imbalance: {value:.3f} (threshold: +/-0.1)")
            recommendations.append("Consider resampling or weighting to balance classes")

        if metric_name = 'DPL' and abs(value) > 0.1:
            issues.append(f"Difference in Positive Labels: {value:.3f}")
            recommendations.append("Review label distribution across groups")

    for metric in report.get('post_training_bias_metrics', []):
        metric_name = metric['name']
        value = metric['value']

        if metric_name = 'DPPL' and abs(value) > 0.1:
            issues.append(f"Demographic Parity: {value:.3f}")
            recommendations.append("Consider model debiasing or threshold adjustment")

        if metric_name = 'DI' and (value < 0.8 or value > 1.25):
            issues.append(f"Disparate Impact: {value:.3f} (should be 0.8-1.25)")
            recommendations.append("Model may violate 80% rule for adverse impact")

    return {
        'issues_found': len(issues) > 0,
        'issues': issues,
        'recommendations': recommendations,
        'full_report': report
    }

# Analyze report
result = analyze_bias_report('my-bucket', 'clarify-output/analysis.json')

if result['issues_found']:
    print("BIAS DETECTED:")
    for issue in result['issues']:
        print(f"  - {issue}")
    print("\nRecommendations:")
    for rec in result['recommendations']:
        print(f"  - {rec}")
else:
    print("No significant bias detected")