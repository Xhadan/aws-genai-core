import json

def lambda_handler(event, context):
    """Handle action group invocations from Bedrock Agent."""

    # Extract action details
    action_group = event.get('actionGroup')
    api_path = event.get('apiPath')
    http_method = event.get('httpMethod')
    parameters = event.get('parameters', [])
    request_body = event.get('requestBody', {})

    # Convert parameters to dict
    params = {p['name']: p['value'] for p in parameters}

    # Route to appropriate handler
    if api_path = '/orders/{orderId}' and http_method = 'GET':
        result = get_order_status(params.get('orderId'))
    elif api_path = '/orders' and http_method = 'POST':
        body = request_body.get('content', {}).get('application/json', {})
        result = create_order(body)
    else:
        result = {'error': f'Unknown action: {api_path}'}

    # Return response in required format
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'apiPath': api_path,
            'httpMethod': http_method,
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(result)
                }
            }
        }
    }

def get_order_status(order_id):
    """Retrieve order status from database."""
    # In production, query actual database
    return {
        'orderId': order_id,
        'status': 'shipped',
        'items': [
            {'productId': 'PROD-001', 'name': 'Widget', 'quantity': 2}
        ],
        'estimatedDelivery': '2025-01-25'
    }

def create_order(body):
    """Create new order in system."""
    # In production, insert into database
    return {
        'orderId': 'ORD-98765',
        'status': 'pending',
        'message': 'Order created successfully'
    }