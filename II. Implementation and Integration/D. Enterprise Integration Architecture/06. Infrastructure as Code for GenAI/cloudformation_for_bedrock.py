# CloudFormation template for Bedrock GenAI infrastructure
CLOUDFORMATION_TEMPLATE = """
AWSTemplateFormatVersion: '2010-09-09'
Description: Bedrock GenAI Infrastructure

Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]
    Default: dev

  KnowledgeBaseName:
    Type: String
    Default: enterprise-kb

  GuardrailName:
    Type: String
    Default: content-guardrail

Resources:
  # IAM Role for Bedrock Agent
  BedrockAgentRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub ${Environment}-bedrock-agent-role
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: bedrock.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonBedrockFullAccess
      Policies:
        - PolicyName: BedrockAgentPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - bedrock:InvokeModel
                  - bedrock:InvokeModelWithResponseStream
                Resource: '*'
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:ListBucket
                Resource:
                  - !GetAtt KnowledgeBaseBucket.Arn
                  - !Sub ${KnowledgeBaseBucket.Arn}/*

  # S3 Bucket for Knowledge Base
  KnowledgeBaseBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub ${Environment}-${KnowledgeBaseName}-${AWS::AccountId}
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true

  # OpenSearch Serverless Collection for Vector Store
  VectorCollection:
    Type: AWS::OpenSearchServerless::Collection
    Properties:
      Name: !Sub ${Environment}-vectors
      Type: VECTORSEARCH

  # Bedrock Guardrail
  ContentGuardrail:
    Type: AWS::Bedrock::Guardrail
    Properties:
      Name: !Sub ${Environment}-${GuardrailName}
      Description: Content safety guardrail
      BlockedInputMessaging: "I cannot process this request due to content policy."
      BlockedOutputsMessaging: "I cannot provide this response due to content policy."
      ContentPolicyConfig:
        FiltersConfig:
          - Type: SEXUAL
            InputStrength: HIGH
            OutputStrength: HIGH
          - Type: VIOLENCE
            InputStrength: HIGH
            OutputStrength: HIGH
          - Type: HATE
            InputStrength: HIGH
            OutputStrength: HIGH
          - Type: INSULTS
            InputStrength: MEDIUM
            OutputStrength: MEDIUM
      TopicPolicyConfig:
        TopicsConfig:
          - Name: CompetitorDiscussion
            Definition: Discussions about competitor products or services
            Examples:
              - "Tell me about competitor X's product"
            Type: DENY

  # Bedrock Knowledge Base
  EnterpriseKnowledgeBase:
    Type: AWS::Bedrock::KnowledgeBase
    Properties:
      Name: !Sub ${Environment}-${KnowledgeBaseName}
      Description: Enterprise knowledge base
      RoleArn: !GetAtt BedrockAgentRole.Arn
      KnowledgeBaseConfiguration:
        Type: VECTOR
        VectorKnowledgeBaseConfiguration:
          EmbeddingModelArn: !Sub arn:aws:bedrock:${AWS::Region}::foundation-model/amazon.titan-embed-text-v2:0
      StorageConfiguration:
        Type: OPENSEARCH_SERVERLESS
        OpensearchServerlessConfiguration:
          CollectionArn: !GetAtt VectorCollection.Arn
          VectorIndexName: enterprise-index
          FieldMapping:
            VectorField: embedding
            TextField: text
            MetadataField: metadata

  # Bedrock Agent
  CustomerServiceAgent:
    Type: AWS::Bedrock::Agent
    Properties:
      AgentName: !Sub ${Environment}-customer-service-agent
      Description: Customer service AI agent
      AgentResourceRoleArn: !GetAtt BedrockAgentRole.Arn
      FoundationModel: anthropic.claude-3-sonnet-20240229-v1:0
      Instruction: |
        You are a helpful customer service agent. Use the knowledge base to answer
        questions about our products and services. Be polite and professional.
      IdleSessionTTLInSeconds: 600
      GuardrailConfiguration:
        GuardrailIdentifier: !GetAtt ContentGuardrail.GuardrailId
        GuardrailVersion: DRAFT

  # Agent Alias for versioning
  AgentAlias:
    Type: AWS::Bedrock::AgentAlias
    Properties:
      AgentId: !GetAtt CustomerServiceAgent.AgentId
      AgentAliasName: !Sub ${Environment}-alias
      Description: Production alias

Outputs:
  AgentId:
    Value: !GetAtt CustomerServiceAgent.AgentId
    Export:
      Name: !Sub ${Environment}-AgentId

  AgentAliasId:
    Value: !GetAtt AgentAlias.AgentAliasId
    Export:
      Name: !Sub ${Environment}-AgentAliasId

  KnowledgeBaseId:
    Value: !GetAtt EnterpriseKnowledgeBase.KnowledgeBaseId
    Export:
      Name: !Sub ${Environment}-KnowledgeBaseId

  GuardrailId:
    Value: !GetAtt ContentGuardrail.GuardrailId
    Export:
      Name: !Sub ${Environment}-GuardrailId
"""