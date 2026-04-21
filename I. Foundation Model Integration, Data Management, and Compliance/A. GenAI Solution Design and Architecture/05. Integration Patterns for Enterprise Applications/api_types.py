import boto3
import json

bedrock = boto3.client('bedrock-runtime')

def lambda_handler(event, context):
    # Extract user input from API Gateway event
    body = json.loads(event.get('body', '{}'))
    user_message = body.get('message', '')

    # Validate input
    if not user_message or len(user_message) > 10000:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid input'})
        }

    try:
        # Invoke Bedrock with Converse API
        response = bedrock.converse(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            messages=[
                {'role': 'user', 'content': [{'text': user_message}]}
            ],
            inferenceConfig={'maxTokens': 1024}
        )

        output = response['output']['message']['content'][0]['text']

        return {
            'statusCode': 200,
            'body': json.dumps({'response': output})
        }

    except bedrock.exceptions.ThrottlingException:
        return {
            'statusCode': 429,
            'body': json.dumps({'error': 'Rate limit exceeded'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal error'})
        }