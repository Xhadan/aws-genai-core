from aws_cdk import (
    Stack,
    aws_bedrock as bedrock,
    aws_iam as iam,
    aws_s3 as s3,
    aws_lambda as lambda_,
    CfnOutput,
    RemovalPolicy,
    Duration,
)
from constructs import Construct

class BedrockGenAIStack(Stack):
    """CDK Stack for Bedrock GenAI infrastructure."""

    def __init__(self, scope: Construct, id: str, environment: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.environment = environment

        # Create IAM role for Bedrock
        self.agent_role = self._create_agent_role()

        # Create S3 bucket for knowledge base
        self.kb_bucket = self._create_kb_bucket()

        # Create Guardrail
        self.guardrail = self._create_guardrail()

        # Create Knowledge Base
        self.knowledge_base = self._create_knowledge_base()

        # Create Agent
        self.agent = self._create_agent()

        # Outputs
        self._create_outputs()

    def _create_agent_role(self) -> iam.Role:
        """Create IAM role for Bedrock agent."""
        role = iam.Role(
            self, "BedrockAgentRole",
            role_name=f"{self.environment}-bedrock-agent-role",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
            ]
        )

        role.add_to_policy(iam.PolicyStatement(
            actions=[
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            resources=["*"]
        ))

        return role

    def _create_kb_bucket(self) -> s3.Bucket:
        """Create S3 bucket for knowledge base documents."""
        bucket = s3.Bucket(
            self, "KnowledgeBaseBucket",
            bucket_name=f"{self.environment}-kb-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN if self.environment = "prod" else RemovalPolicy.DESTROY,
            auto_delete_objects=self.environment != "prod"
        )

        # Grant read access to agent role
        bucket.grant_read(self.agent_role)

        return bucket

    def _create_guardrail(self) -> bedrock.CfnGuardrail:
        """Create Bedrock guardrail."""
        guardrail = bedrock.CfnGuardrail(
            self, "ContentGuardrail",
            name=f"{self.environment}-content-guardrail",
            description="Content safety guardrail",
            blocked_input_messaging="I cannot process this request.",
            blocked_outputs_messaging="I cannot provide this response.",
            content_policy_configdrock.CfnGuardrail.ContentPolicyConfigProperty(
                filters_config=[
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        type="SEXUAL",
                        input_strength="HIGH",
                        output_strength="HIGH"
                    ),
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        type="VIOLENCE",
                        input_strength="HIGH",
                        output_strength="HIGH"
                    ),
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        type="HATE",
                        input_strength="HIGH",
                        output_strength="HIGH"
                    )
                ]
            )
        )

        return guardrail

    def _create_knowledge_base(self) -> bedrock.CfnKnowledgeBase:
        """Create Bedrock knowledge base."""
        knowledge_base = bedrock.CfnKnowledgeBase(
            self, "EnterpriseKB",
            name=f"{self.environment}-enterprise-kb",
            description="Enterprise knowledge base",
            role_arn=self.agent_role.role_arn,
            knowledge_base_configurationdrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
                type="VECTOR",
                vector_knowledge_base_configurationdrock.CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
                    embedding_model_arn=f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0"
                )
            ),
            storage_configurationdrock.CfnKnowledgeBase.StorageConfigurationProperty(
                type="OPENSEARCH_SERVERLESS",
                opensearch_serverless_configurationdrock.CfnKnowledgeBase.OpenSearchServerlessConfigurationProperty(
                    collection_arn="arn:aws:aoss:...",  # Reference actual collection
                    vector_index_name="enterprise-index",
                    field_mappingdrock.CfnKnowledgeBase.OpenSearchServerlessFieldMappingProperty(
                        vector_field="embedding",
                        text_field="text",
                        metadata_field="metadata"
                    )
                )
            )
        )

        return knowledge_base

    def _create_agent(self) -> bedrock.CfnAgent:
        """Create Bedrock agent."""
        agent = bedrock.CfnAgent(
            self, "CustomerServiceAgent",
            agent_name=f"{self.environment}-customer-agent",
            description="Customer service AI agent",
            agent_resource_role_arn=self.agent_role.role_arn,
            foundation_model="anthropic.claude-3-sonnet-20240229-v1:0",
            instruction="""You are a helpful customer service agent.
            Answer questions using the knowledge base. Be professional.""",
            idle_session_ttl_in_seconds`0,
            guardrail_configurationdrock.CfnAgent.GuardrailConfigurationProperty(
                guardrail_identifier=self.guardrail.attr_guardrail_id,
                guardrail_version="DRAFT"
            )
        )

        return agent

    def _create_outputs(self):
        """Create stack outputs."""
        CfnOutput(self, "AgentId",
            value=self.agent.attr_agent_id,
            export_name=f"{self.environment}-AgentId"
        )

        CfnOutput(self, "KnowledgeBaseId",
            value=self.knowledge_base.attr_knowledge_base_id,
            export_name=f"{self.environment}-KnowledgeBaseId"
        )

        CfnOutput(self, "GuardrailId",
            value=self.guardrail.attr_guardrail_id,
            export_name=f"{self.environment}-GuardrailId"
        )


# App entry point
from aws_cdk import App

app = App()

# Deploy to multiple environments
BedrockGenAIStack(app, "GenAI-Dev", environment="dev")
BedrockGenAIStack(app, "GenAI-Prod", environment="prod")

app.synth()