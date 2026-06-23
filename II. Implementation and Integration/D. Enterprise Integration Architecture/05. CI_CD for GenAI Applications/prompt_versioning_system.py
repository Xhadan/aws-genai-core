import json
import hashlib
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, List
import boto3

@dataclass
class PromptVersion:
    """Represents a versioned prompt."""
    prompt_id: str
    version: str
    template: str
    model_id: str
    parameters: Dict
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)

    @property
    def content_hash(self) -> str:
        """Generate hash of prompt content for change detection."""
        content = f"{self.template}{self.model_id}{json.dumps(self.parameters, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]

class PromptVersionManager:
    """Manages prompt versions in DynamoDB."""

    def __init__(self, table_name: str = "prompt-versions"):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def create_version(self, prompt: PromptVersion) -> str:
        """Create a new prompt version."""
        self.table.put_item(Item={
            'prompt_id': prompt.prompt_id,
            'version': prompt.version,
            'template': prompt.template,
            'model_id': prompt.model_id,
            'parameters': prompt.parameters,
            'content_hash': prompt.content_hash,
            'created_at': prompt.created_at,
            'created_by': prompt.created_by,
            'description': prompt.description,
            'tags': prompt.tags
        })
        return prompt.version

    def get_version(self, prompt_id: str, version: str = "latest") -> Optional[PromptVersion]:
        """Get a specific version or latest."""
        if version = "latest":
            # Query for latest version
            response = self.table.query(
                KeyConditionExpression='prompt_id = :pid',
                ExpressionAttributeValues={':pid': prompt_id},
                ScanIndexForwardlse,
                Limit=1
            )
        else:
            response = self.table.get_item(
                Key={'prompt_id': prompt_id, 'version': version}
            )

        items = response.get('Items', [response.get('Item')])
        if not items or items[0] is None:
            return None

        item = items[0]
        return PromptVersion(
            prompt_id=item['prompt_id'],
            version=item['version'],
            template=item['template'],
            model_id=item['model_id'],
            parameters=item['parameters'],
            created_at=item['created_at'],
            created_by=item.get('created_by', ''),
            description=item.get('description', ''),
            tags=item.get('tags', [])
        )

    def list_versions(self, prompt_id: str) -> List[Dict]:
        """List all versions of a prompt."""
        response = self.table.query(
            KeyConditionExpression='prompt_id = :pid',
            ExpressionAttributeValues={':pid': prompt_id}
        )
        return response.get('Items', [])

    def set_production(self, prompt_id: str, version: str):
        """Mark a version as production."""
        # Use a separate table or attribute for deployment status
        self.table.update_item(
            Key={'prompt_id': prompt_id, 'version': version},
            UpdateExpression='SET production = :prod, promoted_at = :time',
            ExpressionAttributeValues={
                ':prod': True,
                ':time': datetime.utcnow().isoformat()
            }
        )

# Example prompt definition file (prompts/summarize.yaml)
PROMPT_CONFIG_EXAMPLE = """
prompt_id: summarize-v1
description: Document summarization prompt
model_id: anthropic.claude-3-sonnet-20240229-v1:0
parameters:
  max_tokens: 1024
  temperature: 0.5
template: |
  You are a professional document analyst. Summarize the following document
  in {num_points} bullet points. Focus on key facts, decisions, and action items.

  Document:
  {document}

  Provide your summary:
tags:
  - summarization
  - documents
"""