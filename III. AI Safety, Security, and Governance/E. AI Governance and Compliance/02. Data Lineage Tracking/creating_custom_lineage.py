import boto3
from sagemaker.lineage.artifact import Artifact
from sagemaker.lineage.context import Context
from sagemaker.lineage.association import Association

sagemaker_client = boto3.client('sagemaker')

def create_genai_pipeline_lineage(
    knowledge_base_s3,
    prompt_template_s3,
    guardrail_id,
    model_id,
    pipeline_name
):
    """
    Create custom lineage for a GenAI RAG pipeline.
    Tracks knowledge base, prompts, guardrails, and model.
    """
    # Create context for the pipeline
    pipeline_context = Context.create(
        context_name=pipeline_name,
        context_type='GenAIPipeline',
        description='RAG-based GenAI application pipeline',
        properties={
            'created_by': 'GenAI Team',
            'environment': 'production'
        }
    )

    # Create artifact for knowledge base
    kb_artifact = Artifact.create(
        artifact_name=f"{pipeline_name}-knowledge-base",
        artifact_type='KnowledgeBase',
        source_uri=knowledge_base_s3,
        properties={
            'document_count': '10000',
            'last_updated': str(datetime.utcnow().date())
        }
    )

    # Create artifact for prompt template
    prompt_artifact = Artifact.create(
        artifact_name=f"{pipeline_name}-prompt-template",
        artifact_type='PromptTemplate',
        source_uri=prompt_template_s3,
        properties={
            'version': '2.0',
            'template_type': 'RAG'
        }
    )

    # Create artifact for guardrail configuration
    guardrail_artifact = Artifact.create(
        artifact_name=f"{pipeline_name}-guardrail",
        artifact_type='Guardrail',
        source_uri=f"arn:aws:bedrock:us-east-1:123456789012:guardrail/{guardrail_id}",
        properties={
            'guardrail_id': guardrail_id,
            'version': 'DRAFT'
        }
    )

    # Create artifact for the foundation model
    model_artifact = Artifact.create(
        artifact_name=f"{pipeline_name}-foundation-model",
        artifact_type='FoundationModel',
        source_uri=f"arn:aws:bedrock:us-east-1::foundation-model/{model_id}",
        properties={
            'model_id': model_id,
            'provider': 'Anthropic'
        }
    )

    # Create associations linking artifacts to pipeline
    Association.create(
        source_arn=kb_artifact.artifact_arn,
        destination_arn=pipeline_context.context_arn,
        association_type='ContributedTo'
    )

    Association.create(
        source_arn=prompt_artifact.artifact_arn,
        destination_arn=pipeline_context.context_arn,
        association_type='ContributedTo'
    )

    Association.create(
        source_arn=guardrail_artifact.artifact_arn,
        destination_arn=pipeline_context.context_arn,
        association_type='AssociatedWith'
    )

    Association.create(
        source_arn=model_artifact.artifact_arn,
        destination_arn=pipeline_context.context_arn,
        association_type='AssociatedWith'
    )

    print(f"GenAI pipeline lineage created: {pipeline_context.context_arn}")

    return {
        'pipeline_context': pipeline_context.context_arn,
        'knowledge_base_artifact': kb_artifact.artifact_arn,
        'prompt_artifact': prompt_artifact.artifact_arn,
        'guardrail_artifact': guardrail_artifact.artifact_arn,
        'model_artifact': model_artifact.artifact_arn
    }


def update_artifact_on_change(artifact_arn, new_source_uri, change_reason):
    """
    Update artifact and maintain audit trail when source changes.
    """
    # Get current artifact
    artifact = Artifact.load(artifact_arn=artifact_arn)

    # Store previous state in properties
    current_props = artifact.properties or {}
    current_props['previous_source'] = artifact.source.source_uri
    current_props['change_reason'] = change_reason
    current_props['change_date'] = str(datetime.utcnow())

    # Update artifact
    artifact.source.source_uri = new_source_uri
    artifact.properties = current_props
    artifact.save()

    print(f"Artifact updated: {artifact_arn}")
    return artifact_arn


# Example: Create lineage for a customer support GenAI app
pipeline_lineage = create_genai_pipeline_lineage(
    knowledge_base_s3='s3://my-bucket/knowledge-base/product-docs/',
    prompt_template_s3='s3://my-bucket/prompts/support-template-v2.json',
    guardrail_id='abc123xyz',
    model_id='anthropic.claude-3-sonnet-20240229-v1:0',
    pipeline_name='customer-support-rag-v2'
)