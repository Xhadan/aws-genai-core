import boto3
from typing import List, Dict, Tuple
import heapq

bedrock = boto3.client('bedrock-runtime')

class TreeOfThoughts:
    """Implement Tree of Thoughts with beam search."""

    def __init__(self, beam_width=3, max_depth=5):
        self.beam_width = beam_width
        self.max_depth = max_depth

    def generate_thoughts(self, problem: str, current_state: str) -> List[str]:
        """Generate possible next thoughts from current state."""
        prompt = f"""Problem: {problem}

Current Progress: {current_state if current_state else "Starting fresh"}

Generate exactly 3 different possible next steps to make progress on this problem.
Each step should be a distinct approach or continuation.

Format:
Thought 1: [first possible approach]
Thought 2: [second possible approach]
Thought 3: [third possible approach]"""

        response = bedrock.converse(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 1024, "temperature": 0.8}
        )

        text = response['output']['message']['content'][0]['text']

        # Parse thoughts
        thoughts = []
        for line in text.split('\n'):
            if line.strip().startswith('Thought'):
                thought = line.split(':', 1)[1].strip() if ':' in line else line
                thoughts.append(thought)

        return thoughts[:3]  # Ensure max 3 thoughts

    def evaluate_thought(self, problem: str, state: str, thought: str) -> float:
        """Evaluate how promising a thought is (0-1 score)."""
        prompt = f"""Problem: {problem}

Current State: {state}

Proposed Next Step: {thought}

Evaluate this next step:
1. Does it make valid progress toward solving the problem? (1-5)
2. Is the reasoning correct and logical? (1-5)
3. How likely is this path to lead to a correct solution? (1-5)

Provide scores for each criterion and a final score from 0 to 1.

Final Score (0-1):"""

        response = bedrock.converse(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 256, "temperature": 0}
        )

        text = response['output']['message']['content'][0]['text']

        # Extract score
        import re
        match = re.search(r'(\d*\.?\d+)', text)
        if match:
            score = float(match.group(1))
            return min(1.0, max(0.0, score))
        return 0.5

    def is_solution(self, problem: str, state: str) -> Tuple[bool, str]:
        """Check if current state is a complete solution."""
        prompt = f"""Problem: {problem}

Current Solution Attempt: {state}

Is this a complete and correct solution to the problem?
Respond with:
COMPLETE: [yes/no]
ANSWER: [the final answer if complete, or "incomplete" if not]"""

        response = bedrock.converse(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 256, "temperature": 0}
        )

        text = response['output']['message']['content'][0]['text'].lower()
        is_complete = 'complete: yes' in text
        answer = ""
        if is_complete and 'answer:' in text:
            answer = text.split('answer:')[1].strip().split('\n')[0]
        return is_complete, answer

    def solve(self, problem: str) -> Dict:
        """Solve problem using beam search Tree of Thoughts."""
        # Priority queue: (negative score, depth, state, path)
        beam = [(0, 0, "", [])]  # Start with empty state

        best_solution = None
        best_score = 0

        for iteration in range(self.max_depth * self.beam_width):
            if not beam:
                break

            # Get best state from beam
            neg_score, depth, state, path = heapq.heappop(beam)

            if depth >= self.max_depth:
                continue

            # Check if we have a solution
            is_sol, answer = self.is_solution(problem, state)
            if is_sol:
                score = -neg_score
                if score > best_score:
                    best_score = score
                    best_solution = {
                        'answer': answer,
                        'path': path,
                        'score': score
                    }
                continue

            # Generate and evaluate next thoughts
            thoughts = self.generate_thoughts(problem, state)

            for thought in thoughts:
                new_state = f"{state}\n{thought}" if state else thought
                score = self.evaluate_thought(problem, state, thought)
                new_path = path + [thought]

                # Add to beam (negative score for min-heap)
                heapq.heappush(beam, (-score, depth + 1, new_state, new_path))

            # Keep only top beam_width items
            beam = heapq.nsmallest(self.beam_width, beam)

        return best_solution if best_solution else {'answer': None, 'path': [], 'score': 0}


# Example usage
tot = TreeOfThoughts(beam_width=3, max_depth=4)

problem = """
Design a cost-effective AWS architecture for a startup's web application.
Requirements:
- Handle 1000 concurrent users
- 99.9% availability
- Monthly budget: $5000
- Auto-scaling based on demand

What specific AWS services should be used and why?
"""

result = tot.solve(problem)
print(f"Solution found with score: {result['score']:.2f}")
print(f"Answer: {result['answer']}")
print(f"\nReasoning path:")
for i, step in enumerate(result['path'], 1):
    print(f"  Step {i}: {step}")