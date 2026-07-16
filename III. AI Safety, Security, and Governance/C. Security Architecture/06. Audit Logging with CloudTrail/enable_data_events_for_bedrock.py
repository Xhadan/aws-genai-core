import boto3

cloudtrail = boto3.client('cloudtrail')

def enable_bedrock_data_events(trail_name):
    """
    Enable CloudTrail data events for Bedrock model invocations.
    """
    response = cloudtrail.put_event_selectors(
        TrailName=trail_name,
        EventSelectors=[
            {
                'ReadWriteType': 'All',
                'IncludeManagementEvents': True,
                'DataResources': [
                    {
                        'Type': 'AWS::Bedrock::Model',
                        'Values': ['arn:aws:bedrock:*']  # All models
                    },
                    {
                        'Type': 'AWS::Bedrock::Guardrail',
                        'Values': ['arn:aws:bedrock:*:*:guardrail/*']
                    }
                ]
            }
        ]
    )
    print(f"Data events enabled for trail: {trail_name}")
    return response

# Alternative: Advanced event selectors for more control
def enable_advanced_selectors(trail_name):
    """
    Use advanced selectors for fine-grained control.
    """
    response = cloudtrail.put_event_selectors(
        TrailName=trail_name,
        AdvancedEventSelectors=[
            {
                'Name': 'Bedrock-Model-Invocations',
                'FieldSelectors': [
                    {
                        'Field': 'eventCategory',
                        'Equals': ['Data']
                    },
                    {
                        'Field': 'resources.type',
                        'Equals': ['AWS::Bedrock::Model']
                    }
                ]
            },
            {
                'Name': 'Bedrock-Management-Events',
                'FieldSelectors': [
                    {
                        'Field': 'eventCategory',
                        'Equals': ['Management']
                    },
                    {
                        'Field': 'eventSource',
                        'Equals': ['bedrock.amazonaws.com']
                    }
                ]
            }
        ]
    )
    return response

enable_bedrock_data_events('my-trail')