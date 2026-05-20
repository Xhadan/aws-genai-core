evaluation_prompt = """
Given the problem and this partial solution:
Problem: [problem]
Partial Solution: [thought]

Rate from 1-5:
- Correctness: Is the reasoning valid?
- Progress: Does this move toward the goal?
- Completeness: How close to a full solution?

Provide your ratings and explanation.
"""