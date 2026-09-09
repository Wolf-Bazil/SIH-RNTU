from typing import Any, Dict
import numpy as np
from backend.agents.base_agent import BaseAgent

class SatelliteEOAgent(BaseAgent):
    """
    Processes satellite Earth observation data to compute hazard index H(x,y,t).
    H(x,y,t) = α * NDVI(x,y,t) + β * LST(x,y,t) + γ * Precipitation(x,y,t)
    where α, β, γ are weighting coefficients.
    """

    def __init__(self, alpha: float = 0.4, beta: float = 0.3, gamma: float = 0.3):
        super().__init__("SatelliteEO")
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Computing hazard index H(x,y,t)")
        # Simulated satellite data
        ndvi = input_data.get("ndvi", np.random.random((100, 100)))
        lst = input_data.get("lst", np.random.random((100, 100)))
        precipitation = input_data.get("precipitation", np.random.random((100, 100)))

        # H(x,y,t) = α * NDVI + β * LST + γ * Precipitation
        H = self.alpha * np.array(ndvi) + self.beta * np.array(lst) + self.gamma * np.array(precipitation)

        return {
            "hazard_index": H.tolist(),
            "mean_hazard": float(np.mean(H)),
            "max_hazard": float(np.max(H)),
            "min_hazard": float(np.min(H))
        }
