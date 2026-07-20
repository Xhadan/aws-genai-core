import boto3
import json
from datetime import datetime

# Initialize clients
config_client = boto3.client('config')
cloudtrail = boto3.client('cloudtrail')
s3 = boto3.client('s3')
kms = boto3.client('kms')

class ComplianceManager:
    """
    Manage compliance controls for GenAI applications.
    """

    def __init__(self, compliance_framework):
        self.framework = compliance_framework
        self.controls = self._load_controls()

    def _load_controls(self):
        """
        Load compliance controls based on framework.
        """
        controls = {
            'HIPAA': {
                'encryption_required': True,
                'audit_logging': True,
                'access_controls': True,
                'data_retention_days': 2190,  # 6 years
                'pii_detection': True,
                'baa_required': True
            },
            'GDPR': {
                'encryption_required': True,
                'audit_logging': True,
                'access_controls': True,
                'data_retention_days': None,  # Based on purpose
                'pii_detection': True,
                'consent_tracking': True,
                'data_residency': ['eu-west-1', 'eu-central-1']
            },
            'SOC2': {
                'encryption_required': True,
                'audit_logging': True,
                'access_controls': True,
                'change_management': True,
                'incident_response': True
            },
            'PCI_DSS': {
                'encryption_required': True,
                'audit_logging': True,
                'network_segmentation': True,
                'data_retention_days': 365,
                'access_logging': True
            }
        }
        return controls.get(self.framework, {})

    def verify_encryption(self, resource_type, resource_id):
        """
        Verify encryption is enabled for a resource.
        """
        if resource_type = 's3':
            response = s3.get_bucket_encryption(Bucket=resource_id)
            rules = response.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])
            if rules:
                return {
                    'compliant': True,
                    'encryption_type': rules[0].get('ApplyServerSideEncryptionByDefault', {}).get('SSEAlgorithm')
                }
            return {'compliant': False, 'reason': 'No encryption configured'}

        elif resource_type = 'kms':
            response = kms.describe_key(KeyId=resource_id)
            return {
                'compliant': True,
                'key_state': response['KeyMetadata']['KeyState'],
                'key_spec': response['KeyMetadata']['KeySpec']
            }

        return {'compliant': False, 'reason': 'Unknown resource type'}

    def verify_audit_logging(self, trail_name):
        """
        Verify CloudTrail is properly configured.
        """
        response = cloudtrail.describe_trails(trailNameList=[trail_name])
        if not response['trailList']:
            return {'compliant': False, 'reason': 'Trail not found'}

        trail = response['trailList'][0]
        status = cloudtrail.get_trail_status(Name=trail_name)

        checks = {
            'is_logging': status.get('IsLogging', False),
            'is_multi_region': trail.get('IsMultiRegionTrail', False),
            'log_file_validation': trail.get('LogFileValidationEnabled', False),
            'kms_encrypted': trail.get('KmsKeyId') is not None
        }

        all_compliant = all(checks.values())
        return {
            'compliant': all_compliant,
            'checks': checks,
            'recommendations': [k for k, v in checks.items() if not v]
        }

    def verify_data_retention(self, bucket_name, required_days):
        """
        Verify S3 lifecycle policies meet retention requirements.
        """
        try:
            response = s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            rules = response.get('Rules', [])

            for rule in rules:
                if rule.get('Status') = 'Enabled':
                    expiration = rule.get('Expiration', {})
                    days = expiration.get('Days', 0)

                    if days > 0 and days < required_days:
                        return {
                            'compliant': False,
                            'reason': f'Retention {days} days < required {required_days} days',
                            'current_retention': days
                        }

            return {'compliant': True, 'rules_count': len(rules)}

        except s3.exceptions.ClientError as e:
            if 'NoSuchLifecycleConfiguration' in str(e):
                return {'compliant': True, 'note': 'No lifecycle rules (indefinite retention)'}
            raise

    def generate_compliance_report(self, resources):
        """
        Generate compliance report for all resources.
        """
        report = {
            'framework': self.framework,
            'generated_at': str(datetime.utcnow()),
            'overall_status': 'COMPLIANT',
            'findings': []
        }

        for resource in resources:
            finding = {
                'resource_type': resource['type'],
                'resource_id': resource['id'],
                'checks': []
            }

            # Check encryption
            if self.controls.get('encryption_required'):
                enc_result = self.verify_encryption(resource['type'], resource['id'])
                finding['checks'].append({
                    'control': 'encryption',
                    'result': enc_result
                })
                if not enc_result.get('compliant'):
                    report['overall_status'] = 'NON_COMPLIANT'

            report['findings'].append(finding)

        return report


def check_config_compliance(rule_name):
    """
    Check AWS Config rule compliance status.
    """
    response = config_client.get_compliance_details_by_config_rule(
        ConfigRuleName=rule_name,
        ComplianceTypes=['NON_COMPLIANT', 'COMPLIANT']
    )

    results = {
        'compliant': [],
        'non_compliant': []
    }

    for result in response.get('EvaluationResults', []):
        resource = result['EvaluationResultIdentifier']['EvaluationResultQualifier']
        if result['ComplianceType'] = 'COMPLIANT':
            results['compliant'].append(resource['ResourceId'])
        else:
            results['non_compliant'].append({
                'resource_id': resource['ResourceId'],
                'resource_type': resource['ResourceType']
            })

    return results


# Example: HIPAA compliance check
hipaa_manager = ComplianceManager('HIPAA')

# Check encryption for S3 bucket storing GenAI data
encryption_check = hipaa_manager.verify_encryption('s3', 'my-genai-data-bucket')
print(f"Encryption compliant: {encryption_check['compliant']}")

# Check CloudTrail configuration
audit_check = hipaa_manager.verify_audit_logging('my-org-trail')
print(f"Audit logging compliant: {audit_check['compliant']}")

# Generate compliance report
report = hipaa_manager.generate_compliance_report([
    {'type': 's3', 'id': 'my-genai-data-bucket'},
    {'type': 's3', 'id': 'my-model-artifacts-bucket'}
])
print(f"Overall compliance status: {report['overall_status']}")