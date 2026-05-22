import boto3
import json
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum

bedrock = boto3.client('bedrock-runtime')

# Define schema using Pydantic
class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class AnalysisResult(BaseModel):
    """Schema for text analysis results."""
    sentiment: Sentiment
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    key_topics: List[str] = Field(min_length=1, description="Main topics found")
    summary: str = Field(min_length, max_lengthP0)
    entities: Optional[List[str]] = None

    @field_validator('confidence')
    @classmethod
    def round_confidence(cls, v):
        return round(v, 2)

class AWSSuggestion(BaseModel):
    """Schema for AWS service suggestions."""
    service: str
    reason: str
    estimated_cost: str
    complexity: str = Field(pattern='^(low|medium|high)$')

class ArchitectureRecommendation(BaseModel):
    """Schema for architecture recommendations."""
    title: str
    description: str
    services: List[AWSSuggestion]
    total_estimated_monthly_cost: str
    implementation_time: str


def validated_json_output(prompt: str, model_class: type[BaseModel], retries: int = 2):
    """Get JSON output validated against Pydantic schema."""

    # Generate schema description from Pydantic model
    schema_json = model_class.model_json_schema()

    full_prompt = f"""{prompt}

Respond with a JSON object that conforms to this schema:
{json.dumps(schema_json, indent=2)}

Return ONLY valid JSON, no other text."""

    for attempt in range(retries + 1):
        response = bedrock.converse(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            messages=[{"role": "user", "content": [{"text": full_prompt}]}],
            inferenceConfig={"maxTokens": 2048, "temperature": 0}
        )

        text = response['output']['message']['content'][0]['text']

        try:
            # Extract JSON if wrapped in markdown
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            data = json.loads(text.strip())
            return model_class.model_validate(data)

        except (json.JSONDecodeError, Exception) as e:
            if attempt < retries:
                # Add error context for retry
                full_prompt += f"\n\nPrevious attempt failed: {str(e)}. Please fix and try again."
            else:
                raise ValueError(f"Failed to get valid JSON after {retries + 1} attempts: {e}")


# Example: Validated analysis
analysis = validated_json_output(
    prompt="Analyze this text: 'The new DynamoDB on-demand pricing is great for variable workloads.'",
    model_class=AnalysisResult
)

print(f"Sentiment: {analysis.sentiment.value}")
print(f"Confidence: {analysis.confidence}")
print(f"Topics: {analysis.key_topics}")

# Example: Architecture recommendation
architecture = validated_json_output(
    prompt="""Recommend an AWS architecture for a startup's web application:
    - 10,000 daily users
    - REST API backend
    - PostgreSQL database
    - File storage needed
    Budget: $500/month""",
    model_class=ArchitectureRecommendation
)

print(f"\nArchitecture: {architecture.title}")
for svc in architecture.services:
    print(f"  - {svc.service}: {svc.reason}")