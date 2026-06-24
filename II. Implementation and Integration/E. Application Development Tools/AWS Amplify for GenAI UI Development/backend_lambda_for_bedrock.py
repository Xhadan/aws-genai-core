import boto3
import json
import os

bedrock_runtime = boto3.client('bedrock-runtime')

def handler(event, context):
    """
    Amplify Lambda function for Bedrock invocation.
    Called via AppSync resolver.
    """

    # Extract from AppSync event
    arguments = event.get('arguments', {})
    identity = event.get('identity', {})

    conversation_id = arguments.get('conversationId')
    message = arguments.get('message')
    user_id = identity.get('sub')

    # Load conversation history from DynamoDB
    history = load_conversation_history(conversation_id)

    # Build messages
    messages = history + [{"role": "user", "content": message}]

    # Invoke Bedrock
    response = bedrock_runtime.invoke_model(
        modelId=os.environ.get('MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0'),
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "system": os.environ.get('SYSTEM_PROMPT', 'You are a helpful assistant.'),
            "messages": messages
        })
    )

    result = json.loads(response['body'].read())
    assistant_message = result['content'][0]['text']

    # Save to DynamoDB
    save_message(conversation_id, user_id, message, 'user')
    save_message(conversation_id, user_id, assistant_message, 'assistant')

    return {
        'conversationId': conversation_id,
        'message': assistant_message,
        'role': 'assistant',
        'createdAt': datetime.utcnow().isoformat()
    }

def stream_handler(event, context):
    """
    Handler for streaming responses via AppSync subscriptions.
    """
    arguments = event.get('arguments', {})
    message = arguments.get('message')
    conversation_id = arguments.get('conversationId')

    # Stream response
    response = bedrock_runtime.invoke_model_with_response_stream(
        modelId=os.environ.get('MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0'),
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": message}]
        })
    )

    full_response = ""

    for event in response['body']:
        chunk = json.loads(event['chunk']['bytes'])

        if chunk['type'] = 'content_block_delta':
            text = chunk['delta'].get('text', '')
            full_response += text

            # Publish to AppSync subscription
            publish_chunk(conversation_id, text)

    # Publish completion
    publish_complete(conversation_id, full_response)

    return {'success': True}

def load_conversation_history(conversation_id: str) -> list:
    """Load conversation history from DynamoDB."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['MESSAGES_TABLE'])

    response = table.query(
        KeyConditionExpression='conversationId = :cid',
        ExpressionAttributeValues={':cid': conversation_id},
        ScanIndexForward=True,
        Limit   # Last 20 messages
    )

    return [
        {"role": item['role'], "content": item['content']}
        for item in response.get('Items', [])
    ]

def save_message(conversation_id: str, user_id: str, content: str, role: str):
    """Save message to DynamoDB."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['MESSAGES_TABLE'])

    table.put_item(Item={
        'conversationId': conversation_id,
        'messageId': str(uuid.uuid4()),
        'userId': user_id,
        'content': content,
        'role': role,
        'createdAt': datetime.utcnow().isoformat()
    })

def publish_chunk(conversation_id: str, chunk: str):
    """Publish chunk to AppSync subscription."""
    # Implementation depends on AppSync setup
    pass

def publish_complete(conversation_id: str, full_response: str):
    """Publish completion to AppSync subscription."""
    pass