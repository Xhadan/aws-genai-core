import boto3
import json
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

bedrock = boto3.client('bedrock-runtime')

# Complex nested schema
class Resource(BaseModel):
    name: str
    type: str
    configuration: Dict[str, str]

class Phase(BaseModel):
    name: str
    duration_weeks: int
    resources: List[Resource]
    milestones: List[str]
    risks: List[str]

class MigrationPlan(BaseModel):
    project_name: str
    total_duration_weeks: int
    total_estimated_cost: str
    phases: List[Phase]
    success_criteria: List[str]


def generate_complex_json(prompt: str, schema_class: type[BaseModel]) -> BaseModel:
    """Generate and validate complex nested JSON."""

    # Build detailed schema description
    schema = schema_class.model_json_schema()

    system_prompt = """You are an expert at generating valid JSON.
Always respond with properly formatted JSON that matches the requested schema.
Ensure all nested objects are complete and valid.
Never include explanatory text outside the JSON."""

    user_prompt = f"""{prompt}

Generate a JSON response conforming to this schema:
{json.dumps(schema, indent=2)}

Important:
- All required fields must be present
- Nested objects must be complete
- Arrays must contain valid elements
- Return ONLY the JSON object"""

    response = bedrock.converse(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        system=[{"text": system_prompt}],
        inferenceConfig={"maxTokens": 4096, "temperature": 0}
    )

    text = response['output']['message']['content'][0]['text']

    # Clean up response
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.split("```")[0]

    data = json.loads(text.strip())
    return schema_class.model_validate(data)


# Generate migration plan
plan = generate_complex_json(
    prompt="""Create a migration plan for moving a monolithic application to AWS microservices.
    Current state: Java monolith on 10 EC2 instances
    Target: Containerized microservices on ECS
    Timeline: 6 months
    Budget: $100,000""",
    schema_class=MigrationPlan
)

print(f"Project: {plan.project_name}")
print(f"Duration: {plan.total_duration_weeks} weeks")
print(f"\nPhases:")
for phase in plan.phases:
    print(f"  {phase.name} ({phase.duration_weeks} weeks)")
    print(f"    Resources: {[r.name for r in phase.resources]}")
    print(f"    Milestones: {phase.milestones}")