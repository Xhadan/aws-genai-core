import json

# Agent Card for a code review agent
agent_card = {
    "name": "CodeReviewAgent",
    "description": "Expert code review agent that analyzes code quality, security, and best practices",
    "version": "1.0.0",
    "url": "https://agents.example.com/code-review",

    # Capabilities this agent offers
    "capabilities": {
        "streaming": True,
        "pushNotifications": True,
        "stateTransitionHistory": True
    },

    # Skills define what the agent can do
    "skills": [
        {
            "id": "review-python",
            "name": "Python Code Review",
            "description": "Review Python code for quality, security, PEP8 compliance, and best practices",
            "inputModes": ["text/plain", "application/x-python"],
            "outputModes": ["application/json", "text/markdown"]
        },
        {
            "id": "review-javascript",
            "name": "JavaScript Code Review",
            "description": "Review JavaScript/TypeScript code for quality and security issues",
            "inputModes": ["text/plain", "application/javascript"],
            "outputModes": ["application/json", "text/markdown"]
        },
        {
            "id": "security-scan",
            "name": "Security Vulnerability Scan",
            "description": "Scan code for known security vulnerabilities and CVEs",
            "inputModes": ["text/plain"],
            "outputModes": ["application/json"]
        }
    ],

    # Authentication requirements
    "authentication": {
        "schemes": ["bearer"],
        "instructions": "Obtain API key from developer portal"
    },

    # Provider information
    "provider": {
        "organization": "Example Corp",
        "url": "https://example.com"
    }
}

# Serve Agent Card at well-known endpoint
# GET https://agents.example.com/.well-known/agent.json
def get_agent_card():
    return json.dumps(agent_card, indent=2)