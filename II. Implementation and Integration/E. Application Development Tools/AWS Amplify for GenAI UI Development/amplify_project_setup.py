# TypeScript configuration for Amplify (shown as reference)
AMPLIFY_CONFIG = '''
// amplify/backend.ts
import { defineBackend } from "@aws-amplify/backend";
import { auth } from "./auth/resource";
import { data } from "./data/resource";

export const backend = defineBackend({
  auth,
  data,
});

// amplify/auth/resource.ts
import { defineAuth } from "@aws-amplify/backend";

export const auth = defineAuth({
  loginWith: {
    email: true,
  },
});

// amplify/data/resource.ts
import { type ClientSchema, a, defineData } from "@aws-amplify/backend";

const schema = a.schema({
  // AI Conversation model
  chat: a.conversation({
    aiModel: a.ai.model("Claude 3 Sonnet"),
    systemPrompt: "You are a helpful assistant.",
  })
  .authorization((allow) => allow.owner()),

  // Custom generation route
  generateSummary: a.generation({
    aiModel: a.ai.model("Claude 3 Haiku"),
    systemPrompt: "Summarize the following text concisely.",
  })
  .arguments({
    text: a.string().required(),
  })
  .returns(a.string())
  .authorization((allow) => allow.authenticated()),
});

export type Schema = ClientSchema<typeof schema>;

export const data = defineData({
  schema,
  authorizationModes: {
    defaultAuthorizationMode: "userPool",
  },
});
'''

print(AMPLIFY_CONFIG)