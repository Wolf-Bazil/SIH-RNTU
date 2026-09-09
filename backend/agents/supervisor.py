from typing import Any, Dict
from backend.agents.base_agent import BaseAgent

class SupervisorAgent(BaseAgent):
    """Orchestrates the multi-agent workflow."""

    def __init__(self):
        super().__init__("Supervisor")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Orchestrating agent workflow")
        # In production, this would coordinate all agents
        return {"status": "workflow_completed", "agents_invoked": []}
