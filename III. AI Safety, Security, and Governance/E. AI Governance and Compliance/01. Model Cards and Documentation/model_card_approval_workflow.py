import boto3
import json

sagemaker = boto3.client('sagemaker')
sns = boto3.client('sns')

def submit_for_review(model_card_name, reviewer_topic_arn):
    """
    Submit Model Card for review and update status.
    """
    # Update status to PendingReview
    current = sagemaker.describe_model_card(ModelCardName=model_card_name)

    sagemaker.update_model_card(
        ModelCardName=model_card_name,
        Content=current['Content'],
        ModelCardStatus='PendingReview'
    )

    # Notify reviewers
    sns.publish(
        TopicArn=reviewer_topic_arn,
        Subject=f"Model Card Review Required: {model_card_name}",
        Message=json.dumps({
            'model_card_name': model_card_name,
            'model_card_arn': current['ModelCardArn'],
            'submitter': 'ML Platform Team',
            'review_url': f"https://console.aws.amazon.com/sagemaker/home#/model-cards/{model_card_name}"
        })
    )

    print(f"Model Card submitted for review: {model_card_name}")


def approve_model_card(model_card_name, approver, comments=""):
    """
    Approve Model Card and update status.
    """
    current = sagemaker.describe_model_card(ModelCardName=model_card_name)
    content = json.loads(current['Content'])

    # Add approval information
    if 'additional_information' not in content:
        content['additional_information'] = {}

    content['additional_information']['approval_info'] = {
        'approved_by': approver,
        'approval_date': str(datetime.utcnow()),
        'comments': comments
    }

    sagemaker.update_model_card(
        ModelCardName=model_card_name,
        Content=json.dumps(content),
        ModelCardStatus='Approved'
    )

    print(f"Model Card approved: {model_card_name}")


def archive_model_card(model_card_name, reason):
    """
    Archive Model Card when model is deprecated.
    """
    current = sagemaker.describe_model_card(ModelCardName=model_card_name)
    content = json.loads(current['Content'])

    content['additional_information']['archive_info'] = {
        'archived_date': str(datetime.utcnow()),
        'archive_reason': reason
    }

    sagemaker.update_model_card(
        ModelCardName=model_card_name,
        Content=json.dumps(content),
        ModelCardStatus='Archived'
    )

    print(f"Model Card archived: {model_card_name}")


def export_model_card_pdf(model_card_name, s3_output_path):
    """
    Export Model Card as PDF for external sharing.
    """
    response = sagemaker.create_model_card_export_job(
        ModelCardName=model_card_name,
        ModelCardVersion=0,  # Latest version
        OutputConfig={
            'S3OutputPath': s3_output_path
        },
        ModelCardExportJobName=f"{model_card_name}-export-{int(datetime.now().timestamp())}"
    )

    print(f"Export job started: {response['ModelCardExportJobArn']}")

    # Wait for export to complete
    waiter = sagemaker.get_waiter('model_card_export_job_completed')
    waiter.wait(ModelCardExportJobArn=response['ModelCardExportJobArn'])

    print(f"Model Card exported to: {s3_output_path}")
    return response['ModelCardExportJobArn']