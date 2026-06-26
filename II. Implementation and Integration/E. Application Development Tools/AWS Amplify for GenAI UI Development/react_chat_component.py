# React/TypeScript code (shown as reference)
REACT_CHAT_CODE = '''
// App.tsx
import { Amplify } from "aws-amplify";
import { Authenticator } from "@aws-amplify/ui-react";
import { AIConversation, createAIHooks } from "@aws-amplify/ui-react-ai";
import { generateClient } from "aws-amplify/data";
import type { Schema } from "../amplify/data/resource";
import outputs from "../amplify_outputs.json";
import "@aws-amplify/ui-react/styles.css";

// Configure Amplify
Amplify.configure(outputs);

// Create typed client
const client = generateClient<Schema>();

// Create AI hooks
const { useAIConversation } = createAIHooks(client);

function ChatInterface() {
  const [
    {
      data: { messages },
      isLoading,
    },
    sendMessage,
  ] = useAIConversation("chat");

  return (
    <AIConversation
      messages={messages}
      isLoading={isLoading}
      handleSendMessage={sendMessage}
      // Custom welcome message
      welcomeMessage={{
        icon: "🤖",
        title: "Welcome to AI Assistant",
        description: "Ask me anything!"
      }}
      // Custom styling
      variant="bubble"
      // Custom message renderer
      messageRenderer={{
        text: ({ text }) => (
          <div className="custom-message">{text}</div>
        ),
      }}
      // Custom actions
      actions={[
        {
          icon: "📋",
          label: "Copy",
          onClick: (message) => navigator.clipboard.writeText(message.content)
        }
      ]}
    />
  );
}

function App() {
  return (
    <Authenticator>
      {({ signOut, user }) => (
        <div className="app">
          <header>
            <h1>AI Chat</h1>
            <span>{user?.signInDetails?.loginId}</span>
            <button onClick={signOut}>Sign out</button>
          </header>
          <main>
            <ChatInterface />
          </main>
        </div>
      )}
    </Authenticator>
  );
}

export default App;
'''

print(REACT_CHAT_CODE)