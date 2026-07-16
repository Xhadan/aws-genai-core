import boto3
from datetime import datetime, timedelta

cloudtrail = boto3.client('cloudtrail')

def lookup_bedrock_events(event_name=None, username=None, hours_back$):
    """
    Query CloudTrail for Bedrock events.
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours_back)

    lookup_attributes = [
        {'AttributeKey': 'EventSource', 'AttributeValue': 'bedrock.amazonaws.com'}
    ]

    if event_name:
        lookup_attributes.append(
            {'AttributeKey': 'EventName', 'AttributeValue': event_name}
        )

    if username:
        lookup_attributes.append(
            {'AttributeKey': 'Username', 'AttributeValue': username}
        )

    events = []
    paginator = cloudtrail.get_paginator('lookup_events')

    for page in paginator.paginate(
        LookupAttributes=lookup_attributes,
        StartTime=start_time,
        EndTime=end_time
    ):
        for event in page.get('Events', []):
            events.append({
                'event_name': event.get('EventName'),
                'event_time': event.get('EventTime'),
                'username': event.get('Username'),
                'source_ip': event.get('CloudTrailEvent', {}).get('sourceIPAddress'),
                'resources': event.get('Resources', [])
            })

    return events

def analyze_security_events(hours_back$):
    """
    Analyze Bedrock events for security insights.
    """
    events = lookup_bedrock_events(hours_back=hours_back)

    analysis = {
        'total_events': len(events),
        'by_event_type': {},
        'by_user': {},
        'suspicious': []
    }

    for event in events:
        # Count by type
        event_name = event['event_name']
        analysis['by_event_type'][event_name] = analysis['by_event_type'].get(event_name, 0) + 1

        # Count by user
        username = event['username']
        analysis['by_user'][username] = analysis['by_user'].get(username, 0) + 1

        # Flag suspicious patterns
        suspicious_events = ['DeleteGuardrail', 'DeleteCustomModel', 'PutModelInvocationLoggingConfiguration']
        if event_name in suspicious_events:
            analysis['suspicious'].append(event)

    return analysis

# Get analysis
analysis = analyze_security_events(hours_backH)
print(f"Total events: {analysis['total_events']}")
print(f"By type: {analysis['by_event_type']}")
print(f"Suspicious events: {len(analysis['suspicious'])}")