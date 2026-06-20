import json
import boto3

bedrock_runtime = boto3.client('bedrock-runtime')

def lambda_handler(event, context):
    """
    Lambda handler for REST API Gateway integration.
    Handles POST /chat endpoint.
    """
    # Parse request
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Invalid JSON'})
        }

    prompt = body.get('prompt')
    model_id = body.get('model', 'anthropic.claude-3-sonnet-20240229-v1:0')
    max_tokens = body.get('max_tokens', 1024)

    if not prompt:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'prompt is required'})
        }

    # Extract user context from API Gateway
    request_context = event.get('requestContext', {})
    user_id = request_context.get('authorizer', {}).get('claims', {}).get('sub')
    api_key_id = request_context.get('identity', {}).get('apiKeyId')

    try:
        # Invoke Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            })
        )

        result = json.loads(response['body'].read())
        output_text = result['content'][0]['text']
        usage = result.get('usage', {})

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'response': output_text,
                'usage': {
                    'input_tokens': usage.get('input_tokens'),
                    'output_tokens': usage.get('output_tokens')
                },
                'model': model_id
            })
        }

    except bedrock_runtime.exceptions.ThrottlingException:
        return {
            'statusCode': 429,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Rate limit exceeded'})
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }


# OpenAPI specification for API Gateway
OPENAPI_SPEC = """
openapi: "3.0.1"
info:
  title: "GenAI API"
  version: "1.0.0"
paths:
  /chat:
    post:
      summary: "Chat with AI"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - prompt
              properties:
                prompt:
                  type: string
                model:
                  type: string
                max_tokens:
                  type: integer
      responses:
        200:
          description: "Successful response"
        400:
          description: "Bad request"
        429:
          description: "Rate limited"
"""