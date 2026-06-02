import requests
import json
from typing import Optional, Dict, Any

class A2AClient:
    """Client for interacting with A2A-compatible agents."""

    def __init__(self, agent_url: str, api_key: Optional[str] = None):
        self.agent_url = agent_url.rstrip('/')
        self.api_key = api_key
        self.agent_card = None

    def _headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def discover(self) -> Dict[str, Any]:
        """Discover agent capabilities via Agent Card."""
        response = requests.get(
            f"{self.agent_url}/.well-known/agent.json",
            headers=self._headers()
        )
        response.raise_for_status()
        self.agent_card = response.json()
        return self.agent_card

    def create_task(self, skill_id: str, input_data: Any) -> str:
        """Create a new task on the remote agent."""
        response = requests.post(
            f"{self.agent_url}/tasks",
            headers=self._headers(),
            json={
                "skill": skill_id,
                "input": input_data
            }
        )
        response.raise_for_status()
        return response.json()["id"]

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get current task status."""
        response = requests.get(
            f"{self.agent_url}/tasks/{task_id}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    def send_message(self, task_id: str, content: str, role: str = "user"):
        """Send a message to an ongoing task."""
        response = requests.post(
            f"{self.agent_url}/tasks/{task_id}/messages",
            headers=self._headers(),
            json={
                "role": role,
                "content": content
            }
        )
        response.raise_for_status()

    def wait_for_completion(self, task_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Poll task until completion."""
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            if status["status"] in ["completed", "failed"]:
                return status
            time.sleep(2)

        raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")


# Example: Using A2A to delegate code review
def delegate_code_review():
    # Connect to code review agent
    client = A2AClient(
        agent_url="https://agents.example.com/code-review",
        api_key="your-api-key"
    )

    # Discover capabilities
    card = client.discover()
    print(f"Agent: {card['name']}")
    print(f"Skills: {[s['id'] for s in card['skills']]}")

    # Create review task
    code_to_review = '''
    def calculate_total(items):
        total = 0
        for item in items:
            total = total + item['price'] * item['quantity']
        return total
    '''

    task_id = client.create_task(
        skill_id="review-python",
        input_data={"code": code_to_review, "focus": ["performance", "best-practices"]}
    )
    print(f"Created task: {task_id}")

    # Wait for results
    result = client.wait_for_completion(task_id)
    print(f"Review complete: {result}")

    return result