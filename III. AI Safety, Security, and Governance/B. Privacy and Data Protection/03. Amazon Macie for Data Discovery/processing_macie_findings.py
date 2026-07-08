import boto3
from datetime import datetime, timedelta

macie = boto3.client('macie2')

def get_recent_findings(days_back=7, severity_filter=None):
    """
    Retrieve recent Macie findings.
    """
    criteria = {
        'createdAt': {
            'gte': int((datetime.now() - timedelta(daysys_back)).timestamp() * 1000)
        },
        'category': {
            'eq': ['CLASSIFICATION']  # Sensitive data findings only
        }
    }

    if severity_filter:
        criteria['severity'] = {'description': {'eq': severity_filter}}

    findings = []
    paginator = macie.get_paginator('list_findings')

    for page in paginator.paginate(
        findingCriteria={'criterion': criteria},
        sortCriteria={'attributeName': 'severity', 'orderBy': 'DESC'}
    ):
        finding_ids = page.get('findingIds', [])
        if finding_ids:
            details = macie.get_findings(findingIds=finding_ids)
            findings.extend(details['findings'])

    return findings

def analyze_genai_data_risks(findings):
    """
    Analyze findings for GenAI-specific risks.
    """
    risk_summary = {
        'total_findings': len(findings),
        'by_severity': {},
        'by_type': {},
        'high_risk_buckets': set(),
        'pii_in_knowledge_bases': [],
        'credentials_detected': []
    }

    for finding in findings:
        # Count by severity
        severity = finding.get('severity', {}).get('description', 'UNKNOWN')
        risk_summary['by_severity'][severity] = risk_summary['by_severity'].get(severity, 0) + 1

        # Analyze sensitive data types
        sensitive_data = finding.get('classificationDetails', {}).get('result', {}).get('sensitiveData', [])
        for data_category in sensitive_data:
            category = data_category.get('category', 'UNKNOWN')
            risk_summary['by_type'][category] = risk_summary['by_type'].get(category, 0) + 1

            # Track high-risk findings
            if category in ['CREDENTIALS', 'FINANCIAL_INFORMATION']:
                bucket = finding.get('resourcesAffected', {}).get('s3Bucket', {}).get('name')
                risk_summary['high_risk_buckets'].add(bucket)

                if category = 'CREDENTIALS':
                    risk_summary['credentials_detected'].append({
                        'bucket': bucket,
                        'key': finding.get('resourcesAffected', {}).get('s3Object', {}).get('key'),
                        'finding_id': finding.get('id')
                    })

        # Check if in knowledge base paths
        object_key = finding.get('resourcesAffected', {}).get('s3Object', {}).get('key', '')
        if 'knowledge-base' in object_key.lower() or 'training' in object_key.lower():
            risk_summary['pii_in_knowledge_bases'].append({
                'path': object_key,
                'types': [d.get('category') for d in sensitive_data]
            })

    return risk_summary

# Get and analyze findings
findings = get_recent_findings(days_back0, severity_filter=['HIGH', 'CRITICAL'])
risk_analysis = analyze_genai_data_risks(findings)

print(f"Total findings: {risk_analysis['total_findings']}")
print(f"By severity: {risk_analysis['by_severity']}")
print(f"High-risk buckets: {risk_analysis['high_risk_buckets']}")
print(f"PII in knowledge bases: {len(risk_analysis['pii_in_knowledge_bases'])}")