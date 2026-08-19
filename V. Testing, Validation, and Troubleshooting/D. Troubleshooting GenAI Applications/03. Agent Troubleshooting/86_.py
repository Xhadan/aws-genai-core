import json
import logging
from typing import Dict, Any

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Action group Lambda with comprehensive debugging.
    """
    # Log full event for debugging
    logger.info(f"Received event: {json.dumps(event, indent=2)}")

    try:
        # Extract action details
        action_group = event.get('actionGroup', '')
        api_path = event.get('apiPath', '')
        http_method = event.get('httpMethod', '')
        parameters = event.get('parameters', [])
        request_body = event.get('requestBody', {})
        session_attributes = event.get('sessionAttributes', {})

        logger.info(f"Action: {action_group} - {http_method} {api_path}")
        logger.info(f"Parameters: {parameters}")

        # Validate required parameters
        param_dict = {p['name']: p['value'] for p in parameters}

        # Route to appropriate handler
        if api_path = '/orders/{orderId}':
            result = handle_get_order(param_dict)
        elif api_path = '/orders':
            result = handle_create_order(request_body)
        else:
            logger.error(f"Unknown API path: {api_path}")
            return create_error_response(
                f"Unknown action: {api_path}",
                400
            )

        logger.info(f"Action result: {json.dumps(result, indent=2)}")

        return create_success_response(result)

    except KeyError as e:
        logger.error(f"Missing required parameter: {e}")
        return create_error_response(
            f"Missing required parameter: {e}",
            400
        )
    except Exception as e:
        logger.exception(f"Action execution failed: {e}")
        return create_error_response(
            f"Internal error: {str(e)}",
            500
        )


def handle_get_order(params: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle order retrieval with validation.
    """
    order_id = params.get('orderId')

    if not order_id:
        raise KeyError('orderId')

    # Simulated order lookup
    return {
        'orderId': order_id,
        'status': 'shipped',
        'items': [
            {'name': 'Widget', 'quantity': 2}
        ],
        'total': 99.99
    }


def handle_create_order(request_body: Dict) -> Dict[str, Any]:
    """
    Handle order creation with validation.
    """
    content = request_body.get('content', {})
    application_json = content.get('application/json', {})
    properties = application_json.get('properties', {})

    items = properties.get('items', {}).get('value', [])

    if not items:
        raise KeyError('items')

    return {
        'orderId': 'ORD-12345',
        'status': 'created',
        'message': f'Order created with {len(items)} items'
    }


def create_success_response(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create properly formatted success response.
    """
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'OrderManagement',
            'apiPath': '/orders',
            'httpMethod': 'GET',
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(body)
                }
            }
        }
    }


def create_error_response(message: str, status_code: int) -> Dict[str, Any]:
    """
    Create properly formatted error response.
    """
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'OrderManagement',
            'apiPath': '/orders',
            'httpMethod': 'GET',
            'httpStatusCode': status_code,
            'responseBody': {
                'application/json': {
                    'body': json.dumps({
                        'error': message
                    })
                }
            }
        }
    }


class ActionGroupDebugger:
    """
    Debug action group configurations and issues.
    """

    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent')
        self.lambda_client = boto3.client('lambda')
        self.logs_client = boto3.client('logs')

    def diagnose_action_group(
        self,
        agent_id: str,
        action_group_id: str
    ) -> Dict[str, Any]:
        """
        Diagnose action group configuration and connectivity.
        """
        diagnosis = {
            'action_group_config': {},
            'lambda_status': {},
            'permission_issues': [],
            'schema_issues': []
        }

        # Get action group details
        try:
            response = self.bedrock_agent.get_agent_action_group(
                agentId=agent_id,
                actionGroupIdtion_group_id,
                agentVersion='DRAFT'
            )

            action_group = response['agentActionGroup']
            diagnosis['action_group_config'] = {
                'name': action_group['actionGroupName'],
                'state': action_group['actionGroupState'],
                'executor_type': action_group.get('actionGroupExecutor', {}).get('type')
            }

            # Check Lambda configuration
            lambda_arn = action_group.get('actionGroupExecutor', {}).get('lambda')
            if lambda_arn:
                diagnosis['lambda_status'] = self._check_lambda(lambda_arn)

            # Check API schema
            api_schema = action_group.get('apiSchema', {})
            if api_schema:
                diagnosis['schema_issues'] = self._validate_schema(api_schema)

        except Exception as e:
            diagnosis['error'] = str(e)

        return diagnosis

    def _check_lambda(self, lambda_arn: str) -> Dict[str, Any]:
        """
        Check Lambda function status and permissions.
        """
        status = {
            'arn': lambda_arn,
            'exists': False,
            'state': None,
            'timeout': None,
            'memory': None,
            'last_error': None
        }

        try:
            response = self.lambda_client.get_function(
                FunctionName=lambda_arn
            )

            config = response['Configuration']
            status['exists'] = True
            status['state'] = config['State']
            status['timeout'] = config['Timeout']
            status['memory'] = config['MemorySize']

            # Check for recent invocation errors
            log_group = f"/aws/lambda/{config['FunctionName']}"
            status['last_error'] = self._get_last_lambda_error(log_group)

        except self.lambda_client.exceptions.ResourceNotFoundException:
            status['error'] = 'Lambda function not found'
        except Exception as e:
            status['error'] = str(e)

        return status

    def _get_last_lambda_error(self, log_group: str) -> str:
        """
        Get most recent Lambda error from CloudWatch.
        """
        try:
            response = self.logs_client.filter_log_events(
                logGroupName=log_group,
                filterPattern='ERROR',
                limit=1
            )

            events = response.get('events', [])
            if events:
                return events[0]['message'][:500]

        except Exception:
            pass

        return None

    def _validate_schema(self, api_schema: Dict) -> List[str]:
        """
        Validate API schema for common issues.
        """
        issues = []

        # Check for S3 schema
        if 's3' in api_schema:
            # S3 schema validation would go here
            pass

        # Check for payload schema
        if 'payload' in api_schema:
            schema = api_schema['payload']

            # Check required fields
            if 'openapi' not in schema:
                issues.append("Missing 'openapi' version in schema")

            if 'paths' not in schema:
                issues.append("Missing 'paths' in schema")
            else:
                for path, methods in schema['paths'].items():
                    for method, spec in methods.items():
                        if 'operationId' not in spec:
                            issues.append(
                                f"Missing operationId for {method.upper()} {path}"
                            )
                        if 'description' not in spec:
                            issues.append(
                                f"Missing description for {method.upper()} {path}"
                            )

        return issues