from typing import Any, Dict

import numpy as np

from backend.agents.base_agent import BaseAgent
from backend.services.ocean_data import derive_drivers, fetch_observations


class MetSentinelAgent(BaseAgent):
    """Computes CI_PFZ from live meteorological and sea state observations.

    CI_PFZ = w1 * Rainfall + w2 * WaveHeight + w3 * PressureDeficit

    The three-term weighted form of the original formula is kept, with the
    land proxies (soil moisture, topographic wetness) replaced by the marine
    drivers that actually set coastal surge risk: sea state and how deep the
    pressure low is. Explicit grids may still be supplied by a caller.
    """

    def __init__(self, w1: float = 0.5, w2: float = 0.3, w3: float = 0.2):
        super().__init__("MetSentinel")
        self.w1 = w1
        self.w2 = w2
        self.w3 = w3

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Computing CI_PFZ")

        if "rainfall_intensity" in input_data and "soil_moisture" in input_data:
            CI = (self.w1 * np.array(input_data["rainfall_intensity"])
                  + self.w2 * np.array(input_data["soil_moisture"])
                  + self.w3 * np.array(input_data.get("topographic_wetness_index", 0.0)))
            return {
                "ci_pfz": CI.tolist(),
                "mean_ci_pfz": float(np.mean(CI)),
                "max_ci_pfz": float(np.max(CI)),
                "live": False,
                "source": "caller-supplied grids",
            }

        obs = input_data.get("observations")
        if obs is None:
            lat = input_data.get("lat")
            lon = input_data.get("lon")
            obs = await (fetch_observations(lat, lon)
                         if lat is not None and lon is not None
                         else fetch_observations())
        drivers = derive_drivers(obs)

        if not obs.get("live"):
            return {
                "ci_pfz": [],
                "mean_ci_pfz": None,
                "live": False,
                "source": "unavailable",
                "detail": "live observation fetch failed",
            }

        terms = {
            "rainfall": (self.w1, drivers["precipitation"]),
            "wave_height": (self.w2, drivers["wave"]),
            "pressure_deficit": (self.w3, drivers["pressure_deficit"]),
        }
        available = {k: (w, v) for k, (w, v) in terms.items() if v is not None}

        if not available:
            return {
                "ci_pfz": [],
                "mean_ci_pfz": None,
                "live": False,
                "source": "unavailable",
                "detail": "no usable drivers in the observation",
            }

        total_weight = sum(w for w, _ in terms.values())
        weight_sum = sum(w for w, _ in available.values())
        CI = sum(w * v for w, v in available.values()) / weight_sum
        confidence = round(weight_sum / total_weight, 3)

        return {
            "mean_ci_pfz": round(float(CI), 4),
            "confidence": confidence,
            "drivers_used": sorted(available),
            "drivers_missing": sorted(set(terms) - set(available)),
            "components": {k: round(float(v), 4) for k, (_, v) in available.items()},
            "observed_at": obs.get("observed_at"),
            "raw": {
                "precipitation_mm": obs.get("precipitation"),
                "wave_height_m": obs.get("wave_height"),
                "wave_period_s": obs.get("wave_period"),
                "pressure_hpa": obs.get("pressure"),
                "sst_c": obs.get("sst"),
            },
            "live": True,
            "source": ", ".join(obs.get("sources", [])),
        }
