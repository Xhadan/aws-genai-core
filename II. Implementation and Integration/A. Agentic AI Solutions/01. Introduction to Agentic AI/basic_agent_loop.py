class AgenticAI:
    """Conceptual agentic AI system."""

    def __init__(self, model, tools, memory):
        self.model = model      # Foundation model for reasoning
        self.tools = tools      # Available actions/APIs
        self.memory = memory    # Persistent context

    def run(self, goal: str) -> str:
        """Execute agent loop until goal achieved."""

        # Load relevant memory
        context = self.memory.retrieve(goal)

        while not self.is_complete(goal):
            # 1. REASON: Decide next action
            plan = self.model.reason(
                goal=goal,
                context=context,
                available_tools=self.tools
            )

            # 2. ACT: Execute chosen action
            if plan.requires_tool:
                result = self.tools.execute(plan.tool_call)
            else:
                result = plan.response

            # 3. OBSERVE: Process result
            context = self.update_context(context, result)

            # 4. PERSIST: Save to memory
            self.memory.store(goal, context, result)

        return self.generate_final_response(goal, context)