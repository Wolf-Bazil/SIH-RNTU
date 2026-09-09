from typing import Any, Dict
import numpy as np
from backend.agents.base_agent import BaseAgent

class PFZReasonerAgent(BaseAgent):
    """
    Combines hazard index H and CI_PFZ to delineate Potential Flood Zones.
    PFZ_Score = λ * H_norm + (1-λ) * CI_PFZ_norm
    """

    def __init__(self, lambda_param: float = 0.6):
        super().__init__("PFZReasoner")
        self.lambda_param = lambda_param

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Delineating Potential Flood Zones")
        H = np.array(input_data.get("hazard_index", []))
        CI = np.array(input_data.get("ci_pfz", []))

        if H.size == 0 or CI.size == 0:
            return {"pfz_score": [], "flood_zones": []}

        # Normalize to [0,1]
        H_norm = (H - np.min(H)) / (np.max(H) - np.min(H) + 1e-8)
        CI_norm = (CI - np.min(CI)) / (np.max(CI) - np.min(CI) + 1e-8)

        # PFZ_Score = λ * H_norm + (1-λ) * CI_norm
        PFZ = self.lambda_param * H_norm + (1 - self.lambda_param) * CI_norm

        # Threshold for flood zone classification
        threshold = 0.7
        flood_zones = (PFZ > threshold).astype(int)

        return {
            "pfz_score": PFZ.tolist(),
            "flood_zones": flood_zones.tolist(),
            "flood_zone_percentage": float(np.mean(flood_zones) * 100)
        }
