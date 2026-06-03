import boto3
import json
from a2a_client import A2AClient  # From previous example

# Lambda function that bridges Bedrock Agent to A2A ecosystem
def lambda_handler(event, context):
    """
    Bedrock Agent action group handler that delegates to A2A agents.
    The agent can use this to invoke specialized external agents.
    """

    action_group = event.get('actionGroup')
    api_path = event.get('apiPath')
    parameters = {p['name']: p['value'] for p in event.get('parameters', [])}

    if api_path = '/delegate-analysis':
        # Delegate to external data analysis agent via A2A
        a2a_client = A2AClient(
            agent_url=parameters['agent_url'],
            api_key=get_secret('a2a-api-key')
        )

        # Create task on remote agent
        task_id = a2a_client.create_task(
            skill_id=parameters['skill'],
            input_data=json.loads(parameters['data'])
        )

        # Wait for completion
        result = a2a_client.wait_for_completion(task_id, timeout`)

        return format_response(event, result)

    elif api_path = '/discover-agents':
        # Discover available agents from registry
        registry_url = parameters.get('registry_url', 'https://a2a-registry.example.com')
        capability = parameters.get('capability')

        # Query registry for agents with required capability
        agents = discover_agents_from_registry(registry_url, capability)

        return format_response(event, {'agents': agents})

    return format_response(event, {'error': 'Unknown action'})

def discover_agents_from_registry(registry_url: str, capability: str):
    """Query A2A registry for agents with specific capability."""
    import requests

    response = requests.get(
        f"{registry_url}/agents",
        params={"capability": capability}
    )

    return response.json().get('agents', [])

def format_response(event, result):
    """Format Lambda response for Bedrock Agent."""
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': event.get('actionGroup'),
            'apiPath': event.get('apiPath'),
            'httpMethod': event.get('httpMethod'),
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(result)
                }
            }
        }
    }

def get_secret(secret_name: str) -> str:
    """Retrieve secret from AWS Secrets Manager."""
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']