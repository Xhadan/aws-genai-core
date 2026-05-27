import boto3
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# Version status lifecycle
class PromptStatus(Enum):
    DRAFT = "draft"
    TESTING = "testing"
    APPROVED = "approved"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

@dataclass
class PromptVersion:
    """Represents a versioned prompt."""
    id: str
    version: str
    template: str
    model_id: str
    status: PromptStatus
    created_at: str
    created_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    changelog: str = ""
    metadata: Dict = None

class PromptVersionManager:
    """Manage prompt versions with governance controls."""

    def __init__(self, dynamodb_table: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(dynamodb_table)
        self.bedrock_agent = boto3.client('bedrock-agent')

    def create_version(self, prompt_id: str, template: str, model_id: str,
                       author: str, changelog: str) -> PromptVersion:
        """Create a new prompt version."""
        # Get latest version number
        latest = self._get_latest_version(prompt_id)
        new_version = self._increment_version(latest.version if latest else "0.0.0")

        version = PromptVersion(
            id=prompt_id,
            version=new_version,
            template=template,
            model_id=model_id,
            status=PromptStatus.DRAFT,
            created_attetime.utcnow().isoformat(),
            created_by=author,
            changelog=changelog,
            metadata={}
        )

        # Store in DynamoDB
        self.table.put_item(Item={
            'pk': f"PROMPT#{prompt_id}",
            'sk': f"VERSION#{new_version}",
            **asdict(version),
            'status': version.status.value
        })

        return version

    def submit_for_approval(self, prompt_id: str, version: str,
                            test_results: Dict) -> bool:
        """Submit version for approval after testing."""
        # Verify tests passed
        if not self._validate_test_results(test_results):
            raise ValueError("Tests must pass before approval submission")

        self._update_status(prompt_id, version, PromptStatus.TESTING)
        return True

    def approve_version(self, prompt_id: str, version: str,
                        approver: str) -> bool:
        """Approve a version for production."""
        # Verify approver has permissions
        if not self._check_approval_permission(approver, prompt_id):
            raise PermissionError("Approver lacks required permissions")

        self.table.update_item(
            Key={'pk': f"PROMPT#{prompt_id}", 'sk': f"VERSION#{version}"},
            UpdateExpression="SET #status = :status, approved_by = :approver, approved_at = :time",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': PromptStatus.APPROVED.value,
                ':approver': approver,
                ':time': datetime.utcnow().isoformat()
            }
        )
        return True

    def deploy_to_production(self, prompt_id: str, version: str,
                             deployer: str) -> str:
        """Deploy approved version to production."""
        # Verify version is approved
        prompt_version = self._get_version(prompt_id, version)
        if prompt_version.status != PromptStatus.APPROVED:
            raise ValueError("Only approved versions can be deployed")

        # Deprecate current production version
        current_prod = self._get_production_version(prompt_id)
        if current_prod:
            self._update_status(prompt_id, current_prod.version, PromptStatus.DEPRECATED)

        # Deploy to Bedrock
        bedrock_arn = self._deploy_to_bedrock(prompt_version)

        # Update status
        self._update_status(prompt_id, version, PromptStatus.PRODUCTION)

        # Log deployment
        self._log_deployment(prompt_id, version, deployer, bedrock_arn)

        return bedrock_arn

    def rollback(self, prompt_id: str, target_version: str,
                 reason: str, executor: str) -> str:
        """Rollback to a previous version."""
        # Verify target version exists and was previously in production
        target = self._get_version(prompt_id, target_version)
        if target.status not in [PromptStatus.DEPRECATED, PromptStatus.APPROVED]:
            raise ValueError("Can only rollback to deprecated or approved versions")

        # Perform rollback
        bedrock_arn = self.deploy_to_production(prompt_id, target_version, executor)

        # Log rollback event
        self._log_rollback(prompt_id, target_version, reason, executor)

        return bedrock_arn

    def get_version_history(self, prompt_id: str) -> List[PromptVersion]:
        """Get all versions of a prompt."""
        response = self.table.query(
            KeyConditionExpression="pk = :pk AND begins_with(sk, :prefix)",
            ExpressionAttributeValues={
                ':pk': f"PROMPT#{prompt_id}",
                ':prefix': "VERSION#"
            }
        )

        versions = []
        for item in response['Items']:
            item['status'] = PromptStatus(item['status'])
            versions.append(PromptVersion(**{k: v for k, v in item.items()
                                             if k not in ['pk', 'sk']}))

        return sorted(versions, key=lambda v: v.version, reverse=True)

    def _increment_version(self, current: str) -> str:
        """Increment patch version."""
        major, minor, patch = map(int, current.split('.'))
        return f"{major}.{minor}.{patch + 1}"

    def _get_latest_version(self, prompt_id: str) -> Optional[PromptVersion]:
        """Get the latest version."""
        history = self.get_version_history(prompt_id)
        return history[0] if history else None

    def _get_version(self, prompt_id: str, version: str) -> PromptVersion:
        """Get specific version."""
        response = self.table.get_item(
            Key={'pk': f"PROMPT#{prompt_id}", 'sk': f"VERSION#{version}"}
        )
        if 'Item' not in response:
            raise ValueError(f"Version {version} not found")
        item = response['Item']
        item['status'] = PromptStatus(item['status'])
        return PromptVersion(**{k: v for k, v in item.items() if k not in ['pk', 'sk']})

    def _update_status(self, prompt_id: str, version: str, status: PromptStatus):
        """Update version status."""
        self.table.update_item(
            Key={'pk': f"PROMPT#{prompt_id}", 'sk': f"VERSION#{version}"},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': status.value}
        )

    def _get_production_version(self, prompt_id: str) -> Optional[PromptVersion]:
        """Get current production version."""
        history = self.get_version_history(prompt_id)
        for v in history:
            if v.status = PromptStatus.PRODUCTION:
                return v
        return None

    def _validate_test_results(self, results: Dict) -> bool:
        """Validate test results meet quality bar."""
        return results.get('passed', False) and results.get('quality_score', 0) > 0.8

    def _check_approval_permission(self, approver: str, prompt_id: str) -> bool:
        """Check if user can approve this prompt."""
        # Implementation would check IAM or custom permissions
        return True

    def _deploy_to_bedrock(self, version: PromptVersion) -> str:
        """Deploy prompt to Bedrock."""
        # Implementation deploys to Bedrock Prompt Management
        return f"arn:aws:bedrock:region:account:prompt/{version.id}:{version.version}"

    def _log_deployment(self, prompt_id: str, version: str,
                        deployer: str, bedrock_arn: str):
        """Log deployment for audit."""
        self.table.put_item(Item={
            'pk': f"AUDIT#{prompt_id}",
            'sk': f"DEPLOY#{datetime.utcnow().isoformat()}",
            'action': 'deploy',
            'version': version,
            'actor': deployer,
            'bedrock_arn': bedrock_arn,
            'timestamp': datetime.utcnow().isoformat()
        })

    def _log_rollback(self, prompt_id: str, version: str,
                      reason: str, executor: str):
        """Log rollback for audit."""
        self.table.put_item(Item={
            'pk': f"AUDIT#{prompt_id}",
            'sk': f"ROLLBACK#{datetime.utcnow().isoformat()}",
            'action': 'rollback',
            'version': version,
            'reason': reason,
            'actor': executor,
            'timestamp': datetime.utcnow().isoformat()
        })


# Example usage
manager = PromptVersionManager("prompt-versions")

# Create new version
version = manager.create_version(
    prompt_id="customer-support",
    template="You are a helpful customer support agent...",
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    author="ai-engineer@company.com",
    changelog="Added enterprise tier handling"
)

print(f"Created version: {version.version}")