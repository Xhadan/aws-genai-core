# Terraform configuration for Bedrock GenAI (main.tf)
TERRAFORM_CONFIG = """
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

variable "environment" {
  type    = string
  default = "dev"
}

# IAM Role for Bedrock Agent
resource "aws_iam_role" "bedrock_agent" {
  name = "${var.environment}-bedrock-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "bedrock_agent_policy" {
  name = "${var.environment}-bedrock-agent-policy"
  role = aws_iam_role.bedrock_agent.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.knowledge_base.arn,
          "${aws_s3_bucket.knowledge_base.arn}/*"
        ]
      }
    ]
  })
}

# S3 Bucket for Knowledge Base
resource "aws_s3_bucket" "knowledge_base" {
  bucket = "${var.environment}-kb-${data.aws_caller_identity.current.account_id}"

  tags = {
    Environment = var.environment
    Purpose     = "BedrockKnowledgeBase"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "knowledge_base" {
  bucket = aws_s3_bucket.knowledge_base.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "knowledge_base" {
  bucket = aws_s3_bucket.knowledge_base.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Bedrock Guardrail
resource "aws_bedrock_guardrail" "content" {
  name                      = "${var.environment}-content-guardrail"
  description               = "Content safety guardrail"
  blocked_input_messaging   = "I cannot process this request due to content policy."
  blocked_outputs_messaging = "I cannot provide this response due to content policy."

  content_policy_config {
    filters_config {
      type            = "SEXUAL"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }

    filters_config {
      type            = "VIOLENCE"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }

    filters_config {
      type            = "HATE"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
  }

  tags = {
    Environment = var.environment
  }
}

# Bedrock Agent
resource "aws_bedrockagent_agent" "customer_service" {
  agent_name              = "${var.environment}-customer-agent"
  description             = "Customer service AI agent"
  agent_resource_role_arn = aws_iam_role.bedrock_agent.arn
  foundation_model        = "anthropic.claude-3-sonnet-20240229-v1:0"
  idle_session_ttl_in_seconds = 600

  instruction = <<-EOT
    You are a helpful customer service agent. Use the knowledge base to answer
    questions about our products and services. Be polite and professional.
  EOT

  guardrail_configuration {
    guardrail_identifier = aws_bedrock_guardrail.content.guardrail_id
    guardrail_version    = "DRAFT"
  }

  tags = {
    Environment = var.environment
  }
}

# Data source
data "aws_caller_identity" "current" {}

# Outputs
output "agent_id" {
  value = aws_bedrockagent_agent.customer_service.agent_id
}

output "guardrail_id" {
  value = aws_bedrock_guardrail.content.guardrail_id
}

output "knowledge_base_bucket" {
  value = aws_s3_bucket.knowledge_base.bucket
}
"""

# Terraform module for reusable GenAI components
TERRAFORM_MODULE = """
# modules/bedrock-agent/main.tf

variable "name" {
  type = string
}

variable "environment" {
  type = string
}

variable "foundation_model" {
  type    = string
  default = "anthropic.claude-3-sonnet-20240229-v1:0"
}

variable "instruction" {
  type = string
}

variable "enable_guardrail" {
  type    = bool
  default = true
}

# ... module resources ...

output "agent_id" {
  value = aws_bedrockagent_agent.this.agent_id
}

output "agent_alias_id" {
  value = aws_bedrockagent_agent_alias.this.agent_alias_id
}
"""