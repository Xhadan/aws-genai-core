# React hooks for custom AI integration (shown as reference)
CUSTOM_HOOKS_CODE = '''
// hooks/useCustomAI.ts
import { generateClient } from "aws-amplify/data";
import { createAIHooks } from "@aws-amplify/ui-react-ai";
import type { Schema } from "../../amplify/data/resource";

const client = generateClient<Schema>();
const { useAIConversation, useAIGeneration } = createAIHooks(client);

// Custom hook for conversation with additional features
export function useEnhancedChat(conversationId?: string) {
  const [
    { data, isLoading, error },
    sendMessage,
  ] = useAIConversation("chat", { id: conversationId });

  // Add custom functionality
  const sendWithContext = async (content: string, context?: object) => {
    const enrichedContent = context
      ? `Context: ${JSON.stringify(context)}\n\nUser: ${content}`
      : content;

    return sendMessage({ content: [{ text: enrichedContent }] });
  };

  const clearHistory = async () => {
    // Custom clear implementation
  };

  return {
    messages: data?.messages || [],
    isLoading,
    error,
    sendMessage: sendWithContext,
    clearHistory,
  };
}

// Hook for one-shot generation
export function useSummaryGenerator() {
  const [{ data, isLoading }, generate] = useAIGeneration("generateSummary");

  const summarize = async (text: string) => {
    return generate({ text });
  };

  return {
    summary: data,
    isLoading,
    summarize,
  };
}

// Custom hook for streaming with manual control
import { useState, useCallback } from "react";

export function useStreamingChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentResponse, setCurrentResponse] = useState("");

  const sendMessage = useCallback(async (content: string) => {
    setMessages((prev) => [...prev, { role: "user", content }]);
    setIsStreaming(true);
    setCurrentResponse("");

    try {
      // Call AppSync subscription for streaming
      const subscription = client.graphql({
        query: streamChat,
        variables: { content },
      }).subscribe({
        next: ({ data }) => {
          setCurrentResponse((prev) => prev + data.chunk);
        },
        complete: () => {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: currentResponse },
          ]);
          setIsStreaming(false);
        },
        error: (err) => {
          console.error("Stream error:", err);
          setIsStreaming(false);
        },
      });

      return () => subscription.unsubscribe();
    } catch (error) {
      setIsStreaming(false);
      throw error;
    }
  }, [currentResponse]);

  return {
    messages,
    isStreaming,
    currentResponse,
    sendMessage,
  };
}
'''

print(CUSTOM_HOOKS_CODE)