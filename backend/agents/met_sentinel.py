from typing import Any, Dict
import numpy as np
from backend.agents.base_agent import BaseAgent

class MetSentinelAgent(BaseAgent):
    """
    Ingests meteorological data and computes CI_PFZ (Critical Index for Potential Flood Zones).
    CI_PFZ = w1 * Rainfall_Intensity + w2 * Soil_Moisture + w3 * Topographic_Wetness_Index
    """

    def __init__(self, w1: float = 0.5, w2: float = 0.3, w3: float = 0.2):
        super().__init__("MetSentinel")
        self.w1 = w1
        self.w2 = w2
        self.w3 = w3

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Computing CI_PFZ")
        rainfall = input_data.get("rainfall_intensity", np.random.random((100, 100)))
        soil_moisture = input_data.get("soil_moisture", np.random.random((100, 100)))
        twi = input_data.get("topographic_wetness_index", np.random.random((100, 100)))

        # CI_PFZ = w1 * Rainfall + w2 * Soil_Moisture + w3 * TWI
        CI_PFZ = self.w1 * np.array(rainfall) + self.w2 * np.array(soil_moisture) + self.w3 * np.array(twi)

        return {
            "ci_pfz": CI_PFZ.tolist(),
            "mean_ci_pfz": float(np.mean(CI_PFZ)),
            "max_ci_pfz": float(np.max(CI_PFZ))
        }
