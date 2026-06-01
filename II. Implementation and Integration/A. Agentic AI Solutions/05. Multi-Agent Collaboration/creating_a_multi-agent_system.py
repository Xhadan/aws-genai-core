import boto3
import time

bedrock_agent = boto3.client('bedrock-agent')

def create_specialized_agent(name: str, instruction: str, description: str):
    """Create a specialized collaborator agent."""
    response = bedrock_agent.create_agent(
        agentName=name,
        foundationModel='anthropic.claude-3-sonnet-20240229-v1:0',
        agentResourceRoleArn='arn:aws:iam::123456789012:role/BedrockAgentRole',
        instruction=instruction,
        descriptionscription  # Critical for supervisor routing decisions
    )
    return response['agent']['agentId']

# Create specialized collaborator agents
billing_agent_id = create_specialized_agent(
    name='billing-specialist',
    instruction='''You are a billing specialist. Help customers with:
    - Invoice inquiries and payment status
    - Billing disputes and adjustments
    - Payment method updates
    - Subscription management''',
    description='Handles all billing, payment, and invoice-related inquiries'
)

technical_agent_id = create_specialized_agent(
    name='technical-support',
    instruction='''You are a technical support specialist. Help customers with:
    - Troubleshooting product issues
    - Configuration guidance
    - Error resolution
    - Performance optimization''',
    description='Handles technical issues, troubleshooting, and product configuration'
)

sales_agent_id = create_specialized_agent(
    name='sales-specialist',
    instruction='''You are a sales specialist. Help customers with:
    - Product information and comparisons
    - Pricing and discounts
    - Upgrade recommendations
    - New feature explanations''',
    description='Handles sales inquiries, product recommendations, and upgrades'
)

# Create supervisor agent
supervisor_response = bedrock_agent.create_agent(
    agentName='customer-service-supervisor',
    foundationModel='anthropic.claude-3-sonnet-20240229-v1:0',
    agentResourceRoleArn='arn:aws:iam::123456789012:role/BedrockAgentRole',
    instruction='''You are a customer service supervisor coordinating a team of specialists.
    Analyze customer requests and route them to the appropriate specialist:
    - Billing issues -> Billing Specialist
    - Technical problems -> Technical Support
    - Sales/product questions -> Sales Specialist

    For complex requests spanning multiple domains, coordinate between specialists
    and synthesize a comprehensive response.''',
    description='Supervisor agent for customer service team'
)

supervisor_id = supervisor_response['agent']['agentId']
print(f"Supervisor Agent ID: {supervisor_id}")