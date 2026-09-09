from typing import Any, Dict
import numpy as np
from backend.agents.base_agent import BaseAgent

class HazardForecasterAgent(BaseAgent):
    """
    Predicts hazard evolution over time using a simple exponential smoothing model.
    H(t+1) = H(t) + η * (H(t) - H(t-1))
    """

    def __init__(self, eta: float = 0.3):
        super().__init__("HazardForecaster")
        self.eta = eta

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Forecasting hazard evolution")
        H_current = np.array(input_data.get("hazard_index", []))
        H_previous = np.array(input_data.get("hazard_previous", H_current))

        if H_current.size == 0:
            return {"forecast": []}

        # H(t+1) = H(t) + η * (H(t) - H(t-1))
        H_forecast = H_current + self.eta * (H_current - H_previous)

        return {
            "forecast": H_forecast.tolist(),
            "mean_forecast": float(np.mean(H_forecast)),
            "trend": "increasing" if np.mean(H_forecast) > np.mean(H_current) else "decreasing"
        }
