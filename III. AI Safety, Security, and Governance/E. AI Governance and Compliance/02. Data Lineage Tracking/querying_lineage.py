import boto3
from sagemaker.lineage.context import Context
from sagemaker.lineage.artifact import Artifact
from sagemaker.lineage.association import Association
from sagemaker.lineage.query import LineageQuery, LineageFilter, LineageSourceEnum

sagemaker_client = boto3.client('sagemaker')

def get_model_lineage(model_artifact_arn):
    """
    Get complete lineage for a model artifact.
    Returns training data, training job, and upstream artifacts.
    """
    # Query backward lineage (what created this model)
    query = LineageQuery()
    query_filter = LineageFilter(
        entities=[LineageSourceEnum.ARTIFACT, LineageSourceEnum.ACTION],
        sources=[LineageSourceEnum.ARTIFACT]
    )

    lineage_response = query.query(
        start_arns=[model_artifact_arn],
        query_filter=query_filter,
        direction='Ascendants',  # Backward lineage
        include_edges=True,
        max_depth
    )

    lineage = {
        'model_arn': model_artifact_arn,
        'training_data': [],
        'training_jobs': [],
        'processing_jobs': [],
        'code_artifacts': []
    }

    for vertex in lineage_response.vertices:
        if vertex.lineage_type = 'artifact':
            artifact = Artifact.load(artifact_arn=vertex.arn)
            if artifact.artifact_type = 'DataSet':
                lineage['training_data'].append({
                    'arn': artifact.artifact_arn,
                    'source_uri': artifact.source.source_uri,
                    'name': artifact.artifact_name
                })
            elif artifact.artifact_type = 'Code':
                lineage['code_artifacts'].append({
                    'arn': artifact.artifact_arn,
                    'source_uri': artifact.source.source_uri
                })

        elif vertex.lineage_type = 'action':
            if 'training' in vertex.arn.lower():
                lineage['training_jobs'].append(vertex.arn)
            elif 'processing' in vertex.arn.lower():
                lineage['processing_jobs'].append(vertex.arn)

    return lineage


def get_dataset_impact(dataset_artifact_arn):
    """
    Find all models and endpoints derived from a dataset.
    Useful for impact analysis when data issues are discovered.
    """
    # Query forward lineage (what was created from this dataset)
    query = LineageQuery()
    query_filter = LineageFilter(
        entities=[LineageSourceEnum.ARTIFACT],
        sources=[LineageSourceEnum.ARTIFACT]
    )

    lineage_response = query.query(
        start_arns=[dataset_artifact_arn],
        query_filter=query_filter,
        direction='Descendants',  # Forward lineage
        include_edges=True,
        max_depth
    )

    impacted = {
        'models': [],
        'endpoints': [],
        'downstream_datasets': []
    }

    for vertex in lineage_response.vertices:
        if vertex.lineage_type = 'artifact':
            artifact = Artifact.load(artifact_arn=vertex.arn)
            if artifact.artifact_type = 'Model':
                impacted['models'].append({
                    'arn': artifact.artifact_arn,
                    'name': artifact.artifact_name
                })
            elif artifact.artifact_type = 'Endpoint':
                impacted['endpoints'].append({
                    'arn': artifact.artifact_arn,
                    'name': artifact.artifact_name
                })
            elif artifact.artifact_type = 'DataSet':
                impacted['downstream_datasets'].append({
                    'arn': artifact.artifact_arn,
                    'source_uri': artifact.source.source_uri
                })

    return impacted


def list_artifacts_by_type(artifact_type, max_results0):
    """
    List all artifacts of a specific type for inventory.
    """
    response = sagemaker_client.list_artifacts(
        SourceUri='s3://',  # Filter by S3 source
        MaxResults=max_results,
        SortBy='CreationTime',
        SortOrder='Descending'
    )

    artifacts = []
    for summary in response['ArtifactSummaries']:
        artifact = sagemaker_client.describe_artifact(
            ArtifactArn=summary['ArtifactArn']
        )
        if artifact.get('ArtifactType') = artifact_type:
            artifacts.append({
                'arn': artifact['ArtifactArn'],
                'name': artifact.get('ArtifactName'),
                'source_uri': artifact.get('Source', {}).get('SourceUri'),
                'created': str(artifact.get('CreationTime'))
            })

    return artifacts


# Example: Find lineage for a deployed model
model_lineage = get_model_lineage(
    'arn:aws:sagemaker:us-east-1:123456789012:artifact/model-abc123'
)

print("== Model Lineage ==")
print(f"Training Data: {len(model_lineage['training_data'])} datasets")
for ds in model_lineage['training_data']:
    print(f"  - {ds['source_uri']}")

print(f"\nTraining Jobs: {len(model_lineage['training_jobs'])}")
for job in model_lineage['training_jobs']:
    print(f"  - {job}")