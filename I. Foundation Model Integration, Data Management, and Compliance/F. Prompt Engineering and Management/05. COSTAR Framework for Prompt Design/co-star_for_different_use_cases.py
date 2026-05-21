import boto3
from dataclasses import dataclass

bedrock = boto3.client('bedrock-runtime')

# Template: Customer Support Response
def create_support_response_prompt(customer_issue: str, customer_tier: str) -> dict:
    """CO-STAR template for customer support responses."""
    return {
        "context": f"""
        Customer support for AWS consulting company.
        Customer tier: {customer_tier}
        Previous interactions: None logged
        Issue reported: {customer_issue}
        """,

        "objective": """
        Provide a helpful response that:
        1. Acknowledges the customer's issue
        2. Explains the likely cause
        3. Provides step-by-step resolution
        4. Offers additional assistance
        """,

        "style": """
        - Clear, step-by-step instructions
        - Use numbered lists for actions
        - Include relevant links/documentation references
        - Keep technical jargon appropriate to context
        """,

        "tone": """
        Empathetic and solution-focused. Validate the customer's
        frustration without being overly apologetic. Confident
        in the resolution while remaining humble.
        """,

        "audience": f"""
        {customer_tier} customer - {'Assume technical background' if customer_tier = 'Enterprise' else 'Explain technical concepts simply'}
        """,

        "response_format": """
        Format:
        - Greeting and acknowledgment (1-2 sentences)
        - Issue understanding (what we think happened)
        - Resolution steps (numbered list)
        - Prevention tips (if applicable)
        - Closing with offer to help further

        Length: 200-300 words
        """
    }


# Template: Technical Documentation
def create_documentation_prompt(feature_name: str, feature_details: str) -> dict:
    """CO-STAR template for technical documentation."""
    return {
        "context": f"""
        Writing documentation for: {feature_name}
        Feature details: {feature_details}
        Documentation platform: Markdown-based wiki
        Existing docs follow AWS documentation style
        """,

        "objective": """
        Create comprehensive documentation that:
        1. Explains what the feature does
        2. Shows how to use it with code examples
        3. Lists configuration options
        4. Covers common use cases
        5. Includes troubleshooting section
        """,

        "style": """
        - AWS documentation style
        - Second person ("you can", "you should")
        - Clear section hierarchy with headers
        - Code blocks with syntax highlighting
        - Tables for configuration options
        - Note/Warning callouts for important info
        """,

        "tone": """
        Neutral and informative. Precise without being dry.
        Helpful without being condescending.
        """,

        "audience": """
        Developers with 2+ years experience. Familiar with
        AWS basics. Looking for quick implementation guidance.
        """,

        "response_format": """
        ## Overview
        ## Prerequisites
        ## Getting Started
        ## Configuration Options (table)
        ## Code Examples
        ## Use Cases
        ## Troubleshooting
        ## Related Resources

        Length: 800-1200 words
        Include at least 2 code examples
        """
    }


# Template: Executive Summary
def create_executive_summary_prompt(topic: str, detailed_content: str) -> dict:
    """CO-STAR template for executive summaries."""
    return {
        "context": f"""
        Topic: {topic}
        Full content to summarize:
        {detailed_content}
        """,

        "objective": """
        Create an executive summary that:
        1. Captures the key points in priority order
        2. Highlights business impact
        3. States clear recommendations
        4. Notes critical risks or dependencies
        """,

        "style": """
        - Bullet points for key findings
        - Bold text for critical numbers/dates
        - Short paragraphs (2-3 sentences max)
        - Lead with conclusions, then support
        """,

        "tone": """
        Confident and direct. Business-focused. No hedging
        on recommendations. Acknowledge uncertainties only
        when material to decisions.
        """,

        "audience": """
        C-level executives with 5 minutes to read. Need to
        make a decision or approve a budget. Want bottom-line
        impact and clear next steps.
        """,

        "response_format": """
        ## Key Findings (3-5 bullets)
        ## Recommendation
        ## Impact Summary (cost, timeline, resources)
        ## Critical Risks (if any)
        ## Requested Action

        Length: 300 words maximum
        """
    }


def invoke_template(template: dict, model_id='anthropic.claude-3-5-sonnet-20241022-v2:0'):
    """Invoke Bedrock with a template-based CO-STAR prompt."""

    system = f"""Context: {template['context']}
Style: {template['style']}
Tone: {template['tone']}
Audience: {template['audience']}"""

    user = f"""{template['objective']}

{template['response_format']}"""

    response = bedrock.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": user}]}],
        system=[{"text": system}],
        inferenceConfig={"maxTokens": 2048, "temperature": 0.7}
    )

    return response['output']['message']['content'][0]['text']


# Example usage
support_template = create_support_response_prompt(
    customer_issue="Lambda function timeout errors during peak hours",
    customer_tier="Enterprise"
)
response = invoke_template(support_template)
print(response)