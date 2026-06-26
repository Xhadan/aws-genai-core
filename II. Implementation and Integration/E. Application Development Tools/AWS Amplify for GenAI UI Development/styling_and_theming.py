# CSS and theme configuration (shown as reference)
STYLING_CODE = '''
// theme.ts - Custom Amplify theme
import { createTheme } from "@aws-amplify/ui-react";

export const aiChatTheme = createTheme({
  name: "ai-chat-theme",
  tokens: {
    colors: {
      primary: {
        10: { value: "#f0f7ff" },
        20: { value: "#e0efff" },
        40: { value: "#b0d4ff" },
        60: { value: "#4da3ff" },
        80: { value: "#0073e6" },
        90: { value: "#005bb5" },
        100: { value: "#004085" },
      },
    },
    components: {
      aiconversation: {
        message: {
          user: {
            backgroundColor: { value: "{colors.primary.80}" },
            color: { value: "white" },
          },
          assistant: {
            backgroundColor: { value: "{colors.neutral.10}" },
            color: { value: "{colors.neutral.100}" },
          },
        },
        input: {
          borderRadius: { value: "24px" },
        },
      },
    },
  },
});

// App.tsx with theme
import { ThemeProvider } from "@aws-amplify/ui-react";
import { aiChatTheme } from "./theme";

function App() {
  return (
    <ThemeProvider theme={aiChatTheme}>
      <Authenticator>
        <ChatInterface />
      </Authenticator>
    </ThemeProvider>
  );
}

// Custom CSS
/*
.amplify-ai-conversation {
  max-width: 800px;
  margin: 0 auto;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.amplify-ai-message--user {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 18px 18px 4px 18px;
}

.amplify-ai-message--assistant {
  background: #f5f5f5;
  border-radius: 18px 18px 18px 4px;
}

.amplify-ai-input {
  border: 2px solid #e0e0e0;
  border-radius: 24px;
  padding: 12px 20px;
  transition: border-color 0.2s;
}

.amplify-ai-input:focus {
  border-color: #667eea;
  outline: none;
}
*/
'''

print(STYLING_CODE)