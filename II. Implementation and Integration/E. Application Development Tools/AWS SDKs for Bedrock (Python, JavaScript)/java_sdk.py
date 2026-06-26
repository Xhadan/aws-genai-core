# Java code (shown as string for reference)
JAVA_SDK_CODE = '''
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.core.SdkBytes;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.bedrockruntime.BedrockRuntimeClient;
import software.amazon.awssdk.services.bedrockruntime.BedrockRuntimeAsyncClient;
import software.amazon.awssdk.services.bedrockruntime.model.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.time.Duration;
import java.util.concurrent.CompletableFuture;

public class BedrockService {

    private final BedrockRuntimeClient syncClient;
    private final BedrockRuntimeAsyncClient asyncClient;
    private final ObjectMapper objectMapper;

    public BedrockService(String region) {
        // Synchronous client
        this.syncClient = BedrockRuntimeClient.builder()
            .region(Region.of(region))
            .credentialsProvider(DefaultCredentialsProvider.create())
            .overrideConfiguration(config -> config
                .apiCallTimeout(Duration.ofMinutes(2))
                .retryPolicy(retry -> retry.numRetries(3)))
            .build();

        // Asynchronous client
        this.asyncClient = BedrockRuntimeAsyncClient.builder()
            .region(Region.of(region))
            .credentialsProvider(DefaultCredentialsProvider.create())
            .build();

        this.objectMapper = new ObjectMapper();
    }

    public String invokeModel(String prompt, String modelId) throws Exception {
        // Build request body
        ObjectNode requestBody = objectMapper.createObjectNode();
        requestBody.put("anthropic_version", "bedrock-2023-05-31");
        requestBody.put("max_tokens", 1024);

        ObjectNode message = objectMapper.createObjectNode();
        message.put("role", "user");
        message.put("content", prompt);
        requestBody.putArray("messages").add(message);

        // Create request
        InvokeModelRequest request = InvokeModelRequest.builder()
            .modelId(modelId)
            .body(SdkBytes.fromUtf8String(objectMapper.writeValueAsString(requestBody)))
            .contentType("application/json")
            .accept("application/json")
            .build();

        // Invoke
        InvokeModelResponse response = syncClient.invokeModel(request);

        // Parse response
        ObjectNode result = objectMapper.readValue(
            response.body().asUtf8String(),
            ObjectNode.class
        );

        return result.get("content").get(0).get("text").asText();
    }

    public CompletableFuture<String> invokeModelAsync(String prompt, String modelId) {
        ObjectNode requestBody = objectMapper.createObjectNode();
        requestBody.put("anthropic_version", "bedrock-2023-05-31");
        requestBody.put("max_tokens", 1024);

        ObjectNode message = objectMapper.createObjectNode();
        message.put("role", "user");
        message.put("content", prompt);
        requestBody.putArray("messages").add(message);

        InvokeModelRequest request = InvokeModelRequest.builder()
            .modelId(modelId)
            .body(SdkBytes.fromUtf8String(requestBody.toString()))
            .contentType("application/json")
            .build();

        return asyncClient.invokeModel(request)
            .thenApply(response -> {
                try {
                    ObjectNode result = objectMapper.readValue(
                        response.body().asUtf8String(),
                        ObjectNode.class
                    );
                    return result.get("content").get(0).get("text").asText();
                } catch (Exception e) {
                    throw new RuntimeException(e);
                }
            });
    }

    // Usage
    public static void main(String[] args) throws Exception {
        BedrockService service = new BedrockService("us-east-1");

        // Sync invocation
        String result = service.invokeModel(
            "Explain machine learning.",
            "anthropic.claude-3-sonnet-20240229-v1:0"
        );
        System.out.println(result);

        // Async invocation
        service.invokeModelAsync("What is AWS?", "anthropic.claude-3-sonnet-20240229-v1:0")
            .thenAccept(System.out::println)
            .join();
    }
}
'''

print(JAVA_SDK_CODE)