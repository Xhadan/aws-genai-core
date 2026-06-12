import boto3
import json

# Your custom agent implementation
class MyCustomAgent:
    def __init__(self, model_client, tools):
        self.model = model_client
        self.tools = tools

    def run(self, input_text, context=None):
        # Your custom agent logic
        messages = [{"role": "user", "content": input_text}]
        if context:
            messages.insert(0, {"role": "system", "content": context})

        # Call model
        response = self.model.invoke(messages)

        # Handle tool calls
        while response.get('tool_calls'):
            for tool_call in response['tool_calls']:
                result = self.tools[tool_call['name']](**tool_call['arguments'])
                messages.append({"role": "tool", "content": json.dumps(result)})
            response = self.model.invoke(messages)

        return response['content']

# Create AgentCore Runtime handler
def handler(event, context):
    """
    Runtime handler that wraps your custom agent.
    This is what AgentCore Runtime invokes.
    """
    # Initialize agent (can be cached)
    agent = MyCustomAgent(model_client, tools)

    # Extract input
    input_text = event.get('inputText')
    session_id = event.get('sessionId')
    memory_context = event.get('memoryContext', {})

    # Run agent with context from AgentCore Memory
    context = "\n".join([m['content'] for m in memory_context.get('memories', [])])
    result = agent.run(input_text, context=context)

    return {
        'output': result,
        'sessionId': session_id
    }

# Deploy to AgentCore
agentcore = boto3.client('bedrock-agentcore')

response = agentcore.create_runtime_endpoint(
    endpointName='custom-agent',
    endpointConfig={
        'agentSource': {
            's3Uri': 's3://my-bucket/agents/custom/'
        },
        'runtime': 'python3.11',
        'handler': 'agent.handler',  # Entry point
        'memoryMB': 512,

        'agentCoreConfig': {
            'memoryId': 'custom-memory-store',
            'gatewayId': 'custom-gateway'
        }
    }
)

# Your custom framework now has:
# - Serverless scaling
# - AgentCore Memory integration
# - Gateway tool access with policies
# - Full observability