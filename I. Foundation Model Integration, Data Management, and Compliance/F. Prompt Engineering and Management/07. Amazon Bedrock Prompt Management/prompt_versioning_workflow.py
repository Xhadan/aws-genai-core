import boto3
from datetime import datetime

bedrock_agent = boto3.client('bedrock-agent')

class PromptVersionManager:
    """Manage prompt versions with safe deployment practices."""

    def __init__(self, prompt_id):
        self.prompt_id = prompt_id
        self.client = boto3.client('bedrock-agent')

    def get_current_version(self):
        """Get the current prompt version."""
        response = self.client.get_prompt(promptIdentifier=self.prompt_id)
        return response.get('version', '1')

    def list_versions(self):
        """List all versions of a prompt."""
        # Note: Actual API may differ - check latest documentation
        response = self.client.list_prompts()
        versions = [
            p for p in response['promptSummaries']
            if p['id'] = self.prompt_id
        ]
        return versions

    def create_new_version(self, new_template, version_notes=""):
        """Create a new version with updated template."""
        # Get current prompt
        current = self.client.get_prompt(promptIdentifier=self.prompt_id)

        # Update variant with new template
        variants = current['variants']
        variants[0]['templateConfiguration']['text']['text'] = new_template

        # Add version notes to description
        description = current.get('description', '')
        if version_notes:
            timestamp = datetime.now().isoformat()
            description += f"\n\n[{timestamp}] {version_notes}"

        response = self.client.update_prompt(
            promptIdentifier=self.prompt_id,
            name=current['name'],
            descriptionscription,
            variants=variants,
            defaultVariant=current['defaultVariant']
        )

        return response['version']

    def compare_versions(self, version_a, version_b):
        """Compare two prompt versions."""
        # Retrieve both versions
        prompt_a = self.client.get_prompt(
            promptIdentifier=self.prompt_id
            # Include version parameter when available
        )
        prompt_b = self.client.get_prompt(
            promptIdentifier=self.prompt_id
        )

        template_a = prompt_a['variants'][0]['templateConfiguration']['text']['text']
        template_b = prompt_b['variants'][0]['templateConfiguration']['text']['text']

        return {
            'version_a': version_a,
            'version_b': version_b,
            'template_a': template_a,
            'template_b': template_b,
            'templates_differ': template_a != template_b
        }


# Example workflow
manager = PromptVersionManager("my-prompt-id")

# Get current version
current = manager.get_current_version()
print(f"Current version: {current}")

# Create new version with improvements
new_template = """You are a helpful customer support agent for an AWS consulting company.

Customer query: {{customer_query}}
Customer tier: {{customer_tier}}
Previous context: {{previous_context}}

IMPORTANT: For Enterprise tier customers, provide detailed technical responses.

Provide a helpful, professional response that:
1. Acknowledges the customer's concern
2. Provides relevant information or solutions
3. Offers next steps if applicable
4. For Enterprise customers, include relevant documentation links

Response:"""

new_version = manager.create_new_version(
    new_template=new_template,
    version_notes="Added Enterprise tier handling and documentation links"
)

print(f"Created version: {new_version}")