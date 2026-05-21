import boto3
from dataclasses import dataclass
from typing import Optional

bedrock = boto3.client('bedrock-runtime')

@dataclass
class COSTARPrompt:
    """Structured CO-STAR prompt builder."""
    context: str
    objective: str
    style: str
    tone: str
    audience: str
    response_format: str

    def build(self) -> str:
        """Build the complete prompt from CO-STAR components."""
        prompt = f"""# Context
{self.context}

# Objective
{self.objective}

# Style
{self.style}

# Tone
{self.tone}

# Audience
{self.audience}

# Response Format
{self.response_format}

---
Please provide your response following all the guidelines above."""

        return prompt

    def build_system_and_user(self) -> tuple:
        """
        Build as system message (Context, Style, Tone, Audience)
        and user message (Objective, Response).
        """
        system = f"""Context: {self.context}

Style Guidelines: {self.style}

Tone: {self.tone}

Audience: {self.audience}"""

        user = f"""{self.objective}

Please format your response as follows:
{self.response_format}"""

        return system, user


def invoke_costar(costar_prompt: COSTARPrompt,
                  model_id='anthropic.claude-3-5-sonnet-20241022-v2:0'):
    """Invoke Bedrock with a CO-STAR structured prompt."""

    system, user = costar_prompt.build_system_and_user()

    response = bedrock.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": user}]}],
        system=[{"text": system}],
        inferenceConfig={
            "maxTokens": 4096,
            "temperature": 0.7
        }
    )

    return response['output']['message']['content'][0]['text']


# Example: Migration plan using CO-STAR
migration_prompt = COSTARPrompt(
    context="""
    You are advising TechCorp, a mid-size e-commerce company with:
    - Current state: Monolithic Java application on 20 EC2 instances
    - Database: Single RDS PostgreSQL instance (500GB)
    - Traffic: 50,000 daily users, 10x spike during sales events
    - Team: 15 developers, 3 DevOps engineers
    - AWS spend: $45,000/month
    - Pain points: Slow deployments (2 weeks), scaling issues during peaks
    """,

    objective="""
    Create a microservices migration strategy that:
    1. Identifies which components to migrate first (prioritized list)
    2. Recommends specific AWS services for each microservice
    3. Provides a phased 9-month timeline
    4. Estimates cost impact (increase during migration, savings after)
    5. Lists key risks and mitigation strategies
    """,

    style="""
    - Technical documentation format
    - Use clear section headers
    - Include tables for comparisons and timelines
    - Provide specific AWS service names and configurations
    - Include architecture decision rationale
    """,

    tone="""
    Professional and confident. Acknowledge the complexity of migration
    while being optimistic about outcomes. Be direct about risks
    without being alarmist. Use collaborative language ("we recommend"
    rather than "you must").
    """,

    audience="""
    Primary: CTO and VP of Engineering (decision makers)
    - Familiar with AWS services
    - Need business justification for budget approval
    - Care about risk mitigation

    Secondary: Technical leads (implementers)
    - Want specific technical guidance
    - Need to estimate team effort
    """,

    response_format="""
    Structure the response as:

    ## Executive Summary (150 words)

    ## Migration Priority Matrix
    | Component | Priority | Reason | AWS Services |

    ## Phase Timeline
    | Phase | Duration | Focus | Deliverables |

    ## Cost Analysis
    - Current monthly cost
    - Migration period cost (9 months)
    - Post-migration monthly cost
    - Break-even timeline

    ## Risk Register
    | Risk | Likelihood | Impact | Mitigation |

    ## Recommendations
    - Immediate actions (next 30 days)
    - Team preparation needs

    Total length: 1500-2000 words
    """
)

# Generate the migration plan
result = invoke_costar(migration_prompt)
print(result)