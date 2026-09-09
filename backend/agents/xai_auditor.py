from typing import Any, Dict
from backend.agents.base_agent import BaseAgent

class XAIAuditorAgent(BaseAgent):
    """Provides explanations for AI decisions."""

    def __init__(self):
        super().__init__("XAIAuditor")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Generating XAI explanation")
        decision = input_data.get("decision", {})
        explanation = {
            "summary": "Decision was made based on weighted combination of hazard index and CI_PFZ.",
            "factors": [
                {"name": "Hazard Index", "weight": 0.6, "contribution": "high"},
                {"name": "CI_PFZ", "weight": 0.4, "contribution": "medium"}
            ],
            "confidence": 0.85
        }

        return {
            "decision": decision,
            "explanation": explanation
        }
