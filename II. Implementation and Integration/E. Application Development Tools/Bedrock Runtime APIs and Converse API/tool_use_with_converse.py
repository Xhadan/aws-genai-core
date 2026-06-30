import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime')

def converse_with_tools(
    messages: list,
    tools: list,
    model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
) -> dict:
    """
    Use Converse API with tool definitions.
    """

    response = bedrock_runtime.converse(
        modelId=model_id,
        messages=messages,
        toolConfig={
            "tools": tools
        },
        inferenceConfig={
            "maxTokens": 1024
        }
    )

    return response

# Define tools
weather_tool = {
    "toolSpec": {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    }
}

calculator_tool = {
    "toolSpec": {
        "name": "calculator",
        "description": "Perform mathematical calculations",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        }
    }
}

def process_tool_use(response: dict) -> list:
    """Process tool use from response and return tool results."""

    tool_results = []
    output = response['output']['message']

    for content in output.get('content', []):
        if 'toolUse' in content:
            tool_use = content['toolUse']
            tool_name = tool_use['name']
            tool_input = tool_use['input']
            tool_use_id = tool_use['toolUseId']

            # Execute tool (mock implementations)
            if tool_name = 'get_weather':
                result = {"temperature": 72, "condition": "sunny"}
            elif tool_name = 'calculator':
                try:
                    result = {"result": eval(tool_input['expression'])}
                except:
                    result = {"error": "Invalid expression"}
            else:
                result = {"error": "Unknown tool"}

            tool_results.append({
                "toolResult": {
                    "toolUseId": tool_use_id,
                    "content": [{"json": result}]
                }
            })

    return tool_results

# Example conversation with tools
messages = [{
    "role": "user",
    "content": [{"text": "What's the weather in Seattle and what is 25 * 4?"}]
}]

tools = [weather_tool, calculator_tool]

# First call - model requests tools
response = converse_with_tools(messages, tools)
print(f"Stop reason: {response['stopReason']}")

if response['stopReason'] = 'tool_use':
    # Add assistant's tool use request
    messages.append(response['output']['message'])

    # Process tools and get results
    tool_results = process_tool_use(response)

    # Add tool results
    messages.append({
        "role": "user",
        "content": tool_results
    })

    # Continue conversation
    final_response = converse_with_tools(messages, tools)
    print(f"Final: {final_response['output']['message']['content'][0]['text']}")