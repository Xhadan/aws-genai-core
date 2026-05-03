from sagemaker.lineage import context, artifact, association

# Get all artifacts associated with a model
model_artifacts = artifact.Artifact.list(
    source_arn='arn:aws:sagemaker:us-east-1:123456789012:model-package/genai-custom-models/1'
)

for art in model_artifacts:
    print(f"Artifact: {art.artifact_name}")
    print(f"  Type: {art.artifact_type}")
    print(f"  Source: {art.source.source_uri}")

    # Get upstream associations (what created this artifact)
    upstream = association.Association.list(
        destination_arn=art.artifact_arn,
        association_type='ContributedTo'
    )
    for assoc in upstream:
        print(f"  Created by: {assoc.source_arn}")