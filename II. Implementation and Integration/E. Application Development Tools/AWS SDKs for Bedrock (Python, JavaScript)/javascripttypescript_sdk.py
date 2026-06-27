# TypeScript/JavaScript code (shown as string for reference)
TYPESCRIPT_SDK_CODE = '''
import {
  BedrockRuntimeClient,
  InvokeModelCommand,
  InvokeModelWithResponseStreamCommand,
} from "@aws-sdk/client-bedrock-runtime";
import {
  BedrockAgentRuntimeClient,
  InvokeAgentCommand,
} from "@aws-sdk/client-bedrock-agent-runtime";

// Configure client
const bedrockRuntime = new BedrockRuntimeClient({
  region: "us-east-1",
  maxAttempts: 3,
  requestTimeout: 120000, // 2 minutes
});

// Types for Claude API
interface ClaudeMessage {
  role: "user" | "assistant";
  content: string;
}

interface ClaudeRequest {
  anthropic_version: string;
  max_tokens: number;
  messages: ClaudeMessage[];
  temperature?: number;
  system?: string;
}

interface ClaudeResponse {
  content: Array<{ type: string; text: string }>;
  usage: { input_tokens: number; output_tokens: number };
  stop_reason: string;
}

// Invoke model function
async function invokeModel(
  prompt: string,
  modelId: string = "anthropic.claude-3-sonnet-20240229-v1:0"
): Promise<string> {
  const request: ClaudeRequest = {
    anthropic_version: "bedrock-2023-05-31",
    max_tokens: 1024,
    messages: [{ role: "user", content: prompt }],
  };

  const command = new InvokeModelCommand({
    modelId,
    body: JSON.stringify(request),
    contentType: "application/json",
    accept: "application/json",
  });

  const response = await bedrockRuntime.send(command);
  const result: ClaudeResponse = JSON.parse(
    new TextDecoder().decode(response.body)
  );

  return result.content[0].text;
}

// Streaming function
async function* streamModel(
  prompt: string,
  modelId: string = "anthropic.claude-3-sonnet-20240229-v1:0"
): AsyncGenerator<string> {
  const command = new InvokeModelWithResponseStreamCommand({
    modelId,
    body: JSON.stringify({
      anthropic_version: "bedrock-2023-05-31",
      max_tokens: 1024,
      messages: [{ role: "user", content: prompt }],
    }),
    contentType: "application/json",
  });

  const response = await bedrockRuntime.send(command);

  if (response.body) {
    for await (const event of response.body) {
      if (event.chunk?.bytes) {
        const chunk = JSON.parse(new TextDecoder().decode(event.chunk.bytes));
        if (chunk.type == "content_block_delta") {
          yield chunk.delta?.text || "";
        }
      }
    }
  }
}

// Usage example
async function main() {
  // Simple invocation
  const result = await invokeModel("What is cloud computing?");
  console.log(result);

  // Streaming
  for await (const chunk of streamModel("Write a haiku about AWS.")) {
    process.stdout.write(chunk);
  }
}

main();
'''

print(TYPESCRIPT_SDK_CODE)