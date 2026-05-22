{
  "variables": [
    {
      "name": "user_query",
      "type": "string",
      "required": true,
      "description": "The user's question"
    },
    {
      "name": "context",
      "type": "string",
      "required": false,
      "default": "general",
      "description": "Domain context for the response"
    },
    {
      "name": "max_length",
      "type": "integer",
      "required": false,
      "default": 500,
      "description": "Maximum response word count"
    }
  ]
}