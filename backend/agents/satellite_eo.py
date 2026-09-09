from typing import Any, Dict

import numpy as np

from backend.agents.base_agent import BaseAgent
from backend.services.ocean_data import derive_drivers, fetch_observations


class SatelliteEOAgent(BaseAgent):
    """Computes the hazard index H(x,y,t) from live observations.

    H(x,y,t) = alpha * SST + beta * Wind + gamma * Precipitation

    The three drivers are normalised onto [0, 1] by
    ``ocean_data.derive_drivers``. This keeps the weighted three-term form of
    the original land formula (NDVI, LST, precipitation) but substitutes the
    marine equivalents the problem statement actually concerns: sea surface
    temperature carries the thermal energy available to a system, and wind and
    rainfall carry its present intensity.

    Callers may still pass explicit ``ndvi`` / ``lst`` / ``precipitation``
    grids, in which case the original gridded computation runs unchanged.
    """

    def __init__(self, alpha: float = 0.4, beta: float = 0.3, gamma: float = 0.3):
        super().__init__("SatelliteEO")
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Computing hazard index H(x,y,t)")

        # Explicit grids win, so the gridded path stays available for when a
        # real raster source is wired in.
        if "ndvi" in input_data and "lst" in input_data:
            H = (self.alpha * np.array(input_data["ndvi"])
                 + self.beta * np.array(input_data["lst"])
                 + self.gamma * np.array(input_data.get("precipitation", 0.0)))
            return {
                "hazard_index": H.tolist(),
                "mean_hazard": float(np.mean(H)),
                "max_hazard": float(np.max(H)),
                "min_hazard": float(np.min(H)),
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
            # No invented numbers: say so instead.
            return {
                "hazard_index": [],
                "mean_hazard": None,
                "live": False,
                "source": "unavailable",
                "detail": "live observation fetch failed",
            }

        terms = {
            "sst": (self.alpha, drivers["sst"]),
            "wind": (self.beta, drivers["wind"]),
            "precipitation": (self.gamma, drivers["precipitation"]),
        }
        available = {k: (w, v) for k, (w, v) in terms.items() if v is not None}

        if not available:
            return {
                "hazard_index": [],
                "mean_hazard": None,
                "live": False,
                "source": "unavailable",
                "detail": "no usable drivers in the observation",
            }

        # Renormalise the weights over whatever drivers came back, so a missing
        # reading does not silently drag the index toward zero.
        total_weight = sum(w for w, _ in terms.values())
        weight_sum = sum(w for w, _ in available.values())
        H = sum(w * v for w, v in available.values()) / weight_sum

        # How much of the three-term model actually had data behind it. An
        # index resting on one driver must not be presented as confidently as
        # one resting on all three.
        confidence = round(weight_sum / total_weight, 3)

        return {
            "mean_hazard": round(float(H), 4),
            "confidence": confidence,
            "drivers_used": sorted(available),
            "drivers_missing": sorted(set(terms) - set(available)),
            "components": {k: round(float(v), 4) for k, (_, v) in available.items()},
            "observed_at": obs.get("observed_at"),
            "location": {"lat": obs.get("lat"), "lon": obs.get("lon")},
            "raw": {
                "sst_c": obs.get("sst"),
                "wind_kmh": obs.get("wind_speed"),
                "precipitation_mm": obs.get("precipitation"),
            },
            "live": True,
            "source": ", ".join(obs.get("sources", [])),
        }
