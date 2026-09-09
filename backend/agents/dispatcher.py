from typing import Any, Dict
from backend.agents.base_agent import BaseAgent
from backend.agents.satellite_eo import SatelliteEOAgent
from backend.agents.met_sentinel import MetSentinelAgent
from backend.agents.pfz_reasoner import PFZReasonerAgent
from backend.agents.hazard_forecaster import HazardForecasterAgent
from backend.agents.boundary_monitor import BoundaryMonitorAgent
from backend.agents.eco_route_planner import EcoRoutePlannerAgent
from backend.agents.multilingual import MultilingualAgent
from backend.agents.xai_auditor import XAIAuditorAgent

class DispatcherAgent(BaseAgent):
    """Routes requests to appropriate agents."""

    def __init__(self):
        super().__init__("Dispatcher")
        self.agents = {
            "satellite_eo": SatelliteEOAgent(),
            "met_sentinel": MetSentinelAgent(),
            "pfz_reasoner": PFZReasonerAgent(),
            "hazard_forecaster": HazardForecasterAgent(),
            "boundary_monitor": BoundaryMonitorAgent(),
            "eco_route_planner": EcoRoutePlannerAgent(),
            "multilingual": MultilingualAgent(),
            "xai_auditor": XAIAuditorAgent()
        }

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Dispatching request")
        agent_name = input_data.get("agent", "satellite_eo")
        agent = self.agents.get(agent_name)

        if agent is None:
            return {"error": f"Agent '{agent_name}' not found"}

        result = await agent.process(input_data.get("data", {}))
        return {"agent": agent_name, "result": result}
