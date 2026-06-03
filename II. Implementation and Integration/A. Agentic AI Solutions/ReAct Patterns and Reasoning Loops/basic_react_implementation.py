import boto3
import json
from typing import List, Dict, Any, Callable

class ReActAgent:
    """A ReAct agent implementation using Amazon Bedrock."""

    def __init__(
        self,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        tools: Dict[str, Callable] = None,
        max_iterations: int = 10
    ):
        self.bedrock = boto3.client('bedrock-runtime')
        self.model_id = model_id
        self.tools = tools or {}
        self.max_iterations = max_iterations

    def _build_system_prompt(self) -> str:
        """Build system prompt with tool descriptions."""
        tool_descriptions = "\n".join([
            f"- {name}: {func.__doc__}"
            for name, func in self.tools.items()
        ])

        return f"""You are a helpful AI assistant that solves problems step by step.

Available tools:
{tool_descriptions}

For each step, respond in this exact format:
Thought: [Your reasoning about what to do next]
Action: [tool_name]
Action Input: [JSON parameters for the tool]

When you have the final answer, respond with:
Thought: [Your final reasoning]
Final Answer: [Your response to the user]

Always reason before acting. Use tools to gather information."""

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response into structured components."""
        result = {"thought": None, "action": None, "action_input": None, "final_answer": None}

        lines = response_text.strip().split('\n')
        for line in lines:
            if line.startswith('Thought:'):
                result["thought"] = line[8:].strip()
            elif line.startswith('Action:'):
                result["action"] = line[7:].strip()
            elif line.startswith('Action Input:'):
                try:
                    result["action_input"] = json.loads(line[13:].strip())
                except json.JSONDecodeError:
                    result["action_input"] = line[13:].strip()
            elif line.startswith('Final Answer:'):
                result["final_answer"] = line[13:].strip()

        return result

    def _invoke_model(self, messages: List[Dict]) -> str:
        """Invoke Bedrock model."""
        response = self.bedrock.converse(
            modelId=self.model_id,
            messages=messages,
            system=[{"text": self._build_system_prompt()}]
        )
        return response['output']['message']['content'][0]['text']

    def run(self, user_query: str) -> str:
        """Execute ReAct loop for user query."""
        messages = [{"role": "user", "content": [{"text": user_query}]}]
        trace = []

        for iteration in range(self.max_iterations):
            # Get LLM response (Thought + Action or Final Answer)
            response_text = self._invoke_model(messages)
            parsed = self._parse_response(response_text)

            trace.append({
                "iteration": iteration + 1,
                "thought": parsed["thought"],
                "action": parsed["action"],
                "action_input": parsed["action_input"]
            })

            # Check for final answer
            if parsed["final_answer"]:
                return parsed["final_answer"]

            # Execute action (tool call)
            if parsed["action"] and parsed["action"] in self.tools:
                tool = self.tools[parsed["action"]]
                try:
                    observation = tool(**parsed["action_input"] if isinstance(parsed["action_input"], dict) else {"input": parsed["action_input"]})
                except Exception as e:
                    observation = f"Error: {str(e)}"

                trace[-1]["observation"] = observation

                # Add observation to conversation
                messages.append({
                    "role": "assistant",
                    "content": [{"text": response_text}]
                })
                messages.append({
                    "role": "user",
                    "content": [{"text": f"Observation: {observation}"}]
                })
            else:
                # No valid action, ask LLM to try again
                messages.append({
                    "role": "assistant",
                    "content": [{"text": response_text}]
                })
                messages.append({
                    "role": "user",
                    "content": [{"text": "Please provide a valid action or final answer."}]
                })

        return "Max iterations reached without final answer."


# Example tools
def search_database(query: str) -> str:
    """Search the product database for items matching the query."""
    # Simulated database search
    return json.dumps([
        {"id": "PROD-001", "name": "Widget Pro", "price": 99.99},
        {"id": "PROD-002", "name": "Widget Basic", "price": 49.99}
    ])

def get_order_status(order_id: str) -> str:
    """Get the current status of an order by its ID."""
    # Simulated order lookup
    return json.dumps({
        "order_id": order_id,
        "status": "shipped",
        "estimated_delivery": "2025-01-25"
    })


# Use the agent
agent = ReActAgent(
    tools={
        "search_database": search_database,
        "get_order_status": get_order_status
    }
)

result = agent.run("Find widgets under $75 and check if order ORD-123 has shipped")
print(result)