# GraphQL Schema (schema.graphql)
GRAPHQL_SCHEMA = """
type Query {
    # Simple completion
    complete(prompt: String!, maxTokens: Int): CompletionResponse!

    # Conversation with history
    chat(messages: [MessageInput!]!, conversationId: String): ChatResponse!
}

type Mutation {
    # Start a new conversation
    startConversation: Conversation!

    # Send message to conversation
    sendMessage(conversationId: String!, message: String!): ChatResponse!
}

type Subscription {
    # Real-time streaming for chat
    onMessageStream(conversationId: String!): StreamChunk
        @aws_subscribe(mutations: ["streamMessage"])
}

input MessageInput {
    role: String!
    content: String!
}

type CompletionResponse {
    text: String!
    inputTokens: Int
    outputTokens: Int
    model: String
}

type ChatResponse {
    message: String!
    conversationId: String!
    usage: UsageInfo
}

type StreamChunk {
    text: String
    done: Boolean
    conversationId: String!
}

type Conversation {
    id: String!
    createdAt: String!
}

type UsageInfo {
    inputTokens: Int
    outputTokens: Int
}
"""

# Lambda resolver for 'complete' query
import json
import boto3

bedrock_runtime = boto3.client('bedrock-runtime')

def appsync_resolver(event, context):
    """
    AppSync Lambda resolver for GenAI operations.
    """
    field_name = event.get('fieldName')
    arguments = event.get('arguments', {})
    identity = event.get('identity', {})

    if field_name = 'complete':
        return handle_complete(arguments)
    elif field_name = 'chat':
        return handle_chat(arguments)
    elif field_name = 'startConversation':
        return handle_start_conversation(identity)
    elif field_name = 'sendMessage':
        return handle_send_message(arguments)
    else:
        raise Exception(f"Unknown field: {field_name}")

def handle_complete(args):
    """Handle simple completion query."""
    prompt = args['prompt']
    max_tokens = args.get('maxTokens', 1024)

    response = bedrock_runtime.invoke_model(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        })
    )

    result = json.loads(response['body'].read())
    usage = result.get('usage', {})

    return {
        'text': result['content'][0]['text'],
        'inputTokens': usage.get('input_tokens'),
        'outputTokens': usage.get('output_tokens'),
        'model': 'anthropic.claude-3-sonnet-20240229-v1:0'
    }

def handle_chat(args):
    """Handle multi-turn chat."""
    messages = args['messages']
    conversation_id = args.get('conversationId', 'default')

    # Convert GraphQL messages to Bedrock format
    bedrock_messages = [
        {"role": m['role'], "content": m['content']}
        for m in messages
    ]

    response = bedrock_runtime.invoke_model(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": bedrock_messages
        })
    )

    result = json.loads(response['body'].read())
    usage = result.get('usage', {})

    return {
        'message': result['content'][0]['text'],
        'conversationId': conversation_id,
        'usage': {
            'inputTokens': usage.get('input_tokens'),
            'outputTokens': usage.get('output_tokens')
        }
    }