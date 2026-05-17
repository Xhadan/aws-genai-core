import boto3

bedrock = boto3.client('bedrock-runtime')

class ConversationManager:
    """Manage multi-turn conversations with proper message structure."""

    def __init__(self, system_prompt, model_id='anthropic.claude-3-5-sonnet-20241022-v2:0'):
        self.system_prompt = system_prompt
        self.model_id = model_id
        self.messages = []

    def add_user_message(self, content):
        """Add a user message to the conversation."""
        self.messages.append({
            "role": "user",
            "content": [{"text": content}]
        })

    def add_assistant_message(self, content):
        """Add an assistant message (from model response)."""
        self.messages.append({
            "role": "assistant",
            "content": [{"text": content}]
        })

    def get_response(self, user_input):
        """Get model response and update conversation history."""
        self.add_user_message(user_input)

        response = bedrock.converse(
            modelId=self.model_id,
            messages=self.messages,
            system=[{"text": self.system_prompt}],
            inferenceConfig={
                "maxTokens": 2048,
                "temperature": 0.7
            }
        )

        assistant_response = response['output']['message']['content'][0]['text']
        self.add_assistant_message(assistant_response)

        return assistant_response


# Example multi-turn conversation
system = """You are an AWS cost optimization specialist. Help users reduce
their AWS bills while maintaining performance and reliability. Ask clarifying
questions when needed."""

conversation = ConversationManager(system)

# Turn 1
response1 = conversation.get_response(
    "My AWS bill is $50,000/month and I want to reduce it."
)
print("Assistant:", response1)

# Turn 2 - Context is maintained
response2 = conversation.get_response(
    "We're running 50 EC2 instances, mostly m5.xlarge, running 24/7."
)
print("Assistant:", response2)

# Turn 3 - Continues with full context
response3 = conversation.get_response(
    "About 30% of them are for dev/test environments."
)
print("Assistant:", response3)