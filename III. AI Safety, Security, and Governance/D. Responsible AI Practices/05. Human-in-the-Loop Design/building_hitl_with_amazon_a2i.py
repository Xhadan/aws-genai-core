import boto3
import json
from datetime import datetime

a2i = boto3.client('sagemaker-a2i-runtime')
sagemaker = boto3.client('sagemaker')

def create_human_review_flow(
    flow_name,
    task_template_arn,
    workteam_arn,
    confidence_threshold=0.7
):
    """
    Create an A2I flow definition for human review.
    """
    # Flow definition specifies when human review is triggered
    flow_definition = sagemaker.create_flow_definition(
        FlowDefinitionName=flow_name,
        HumanLoopConfig={
            'WorkteamArn': workteam_arn,
            'HumanTaskUiArn': task_template_arn,
            'TaskTitle': 'Review AI Output',
            'TaskDescription': 'Review and verify the AI-generated content',
            'TaskCount': 1,  # Number of reviewers per task
            'TaskAvailabilityLifetimeInSeconds': 3600,  # 1 hour
            'TaskTimeLimitInSeconds': 600,  # 10 minutes per task
            'PublicWorkforceTaskPrice': {
                'AmountInUsd': {
                    'Dollars': 0,
                    'Cents': 5,  # $0.05 per task
                    'TenthFractionsOfACent': 0
                }
            }
        },
        HumanLoopRequestSource={
            'AwsManagedHumanLoopRequestSource': 'AWS/Textract/AnalyzeDocument/Forms/V1'
        },
        HumanLoopActivationConfig={
            'HumanLoopActivationConditionsConfig': {
                'HumanLoopActivationConditions': json.dumps({
                    'Conditions': [
                        {
                            'ConditionType': 'Sampling',
                            'ConditionParameters': {
                                'RandomSamplingPercentage': 10  # 10% sampling
                            }
                        },
                        {
                            'Or': [
                                {
                                    'ConditionType': 'ImportantFormKeyConfidenceCheck',
                                    'ConditionParameters': {
                                        'ImportantFormKey': '*',
                                        'KeyValueBlockConfidenceLessThan': confidence_threshold
                                    }
                                }
                            ]
                        }
                    ]
                })
            }
        },
        OutputConfig={
            'S3OutputPath': 's3://my-bucket/a2i-output/'
        },
        RoleArn='arn:aws:iam::123456789012:role/A2IRole'
    )

    print(f"Flow definition created: {flow_definition['FlowDefinitionArn']}")
    return flow_definition['FlowDefinitionArn']


def start_human_loop(
    flow_definition_arn,
    content_to_review,
    input_data,
    human_loop_name=None
):
    """
    Start a human review loop for specific content.
    """
    if not human_loop_name:
        human_loop_name = f"review-{int(datetime.now().timestamp())}"

    response = a2i.start_human_loop(
        HumanLoopName=human_loop_name,
        FlowDefinitionArn=flow_definition_arn,
        HumanLoopInput={
            'InputContent': json.dumps({
                'content': content_to_review,
                'metadata': input_data,
                'timestamp': str(datetime.utcnow())
            })
        },
        DataAttributes={
            'ContentClassifiers': [
                'FreeOfPersonallyIdentifiableInformation',
                'FreeOfAdultContent'
            ]
        }
    )

    print(f"Human loop started: {response['HumanLoopArn']}")
    return response['HumanLoopArn']


def check_human_loop_status(human_loop_name):
    """
    Check status of human review loop.
    """
    response = a2i.describe_human_loop(
        HumanLoopName=human_loop_name
    )

    status = response['HumanLoopStatus']
    print(f"Human loop status: {status}")

    if status = 'Completed':
        # Get human review output
        output = response.get('HumanLoopOutput', {})
        return {
            'status': 'completed',
            'output_s3': output.get('OutputS3Uri'),
            'completion_time': str(response.get('HumanLoopOutput', {}).get('CompletionTime'))
        }
    elif status = 'Failed':
        return {
            'status': 'failed',
            'failure_reason': response.get('FailureReason')
        }
    else:
        return {
            'status': status,
            'message': 'Review in progress'
        }


# Example: Human review for GenAI output
def review_genai_output(ai_response, confidence, threshold=0.7):
    """
    Route GenAI output to human review if confidence is low.
    """
    if confidence < threshold:
        print(f"Low confidence ({confidence:.2f}), routing to human review")
        loop_arn = start_human_loop(
            flow_definition_arn='arn:aws:sagemaker:us-east-1:123456789012:flow-definition/genai-review',
            content_to_review=ai_response,
            input_data={
                'confidence': confidence,
                'model': 'claude-3-sonnet',
                'use_case': 'customer_support'
            }
        )
        return {'status': 'pending_review', 'human_loop_arn': loop_arn}
    else:
        return {'status': 'auto_approved', 'response': ai_response}