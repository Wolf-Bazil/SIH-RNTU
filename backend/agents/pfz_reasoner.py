from typing import Any, Dict

import numpy as np

from backend.agents.base_agent import BaseAgent
from backend.services.ocean_data import fetch_observations


class PFZReasonerAgent(BaseAgent):
    """Scores a location as a Potential Fishing Zone from live sea state.

    PFZ_Score = lambda * SST_suitability + (1 - lambda) * Sea_state_suitability

    Pelagic shoals in the Indian EEZ concentrate where the water sits in a
    roughly 27-29 C band, and small mechanised craft can only work it when the
    sea is workable. Both terms are therefore peaked, not monotonic: water that
    is too warm is as unsuitable as water that is too cold, which is why this
    cannot reuse the plain min-max normalisation the hazard agents use.

    The gridded path is preserved for callers that supply H and CI_PFZ arrays.
    """

    def __init__(self, lambda_param: float = 0.6):
        super().__init__("PFZReasoner")
        self.lambda_param = lambda_param

    @staticmethod
    def _peak(value: float, ideal_low: float, ideal_high: float,
              falloff: float) -> float:
        """1.0 inside the ideal band, tapering linearly to 0 over `falloff`."""
        if ideal_low <= value <= ideal_high:
            return 1.0
        distance = ideal_low - value if value < ideal_low else value - ideal_high
        return max(0.0, 1.0 - distance / falloff)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Delineating Potential Fishing Zones")

        H = np.array(input_data.get("hazard_index", []))
        CI = np.array(input_data.get("ci_pfz", []))
        if H.size and CI.size:
            H_norm = (H - np.min(H)) / (np.max(H) - np.min(H) + 1e-8)
            CI_norm = (CI - np.min(CI)) / (np.max(CI) - np.min(CI) + 1e-8)
            PFZ = self.lambda_param * H_norm + (1 - self.lambda_param) * CI_norm
            flood_zones = (PFZ > 0.7).astype(int)
            return {
                "pfz_score": PFZ.tolist(),
                "flood_zones": flood_zones.tolist(),
                "flood_zone_percentage": float(np.mean(flood_zones) * 100),
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

        sst = obs.get("sst")
        wave = obs.get("wave_height")
        wind = obs.get("wind_speed")

        if not obs.get("live") or sst is None:
            return {
                "pfz_score": None,
                "live": False,
                "source": "unavailable",
                "detail": "live observation fetch failed",
            }

        # 27-29 C is the productive band for pelagic species in this basin;
        # suitability tapers to zero about 4 C outside it.
        sst_suitability = self._peak(sst, 27.0, 29.0, 4.0)

        # Workable sea for small craft: under 1.5 m and under 25 km/h, tapering
        # out at the 3 m INCOIS warning level.
        wave_ok = 1.0 if wave is None else max(0.0, 1.0 - max(0.0, wave - 1.5) / 1.5)
        wind_ok = 1.0 if wind is None else max(0.0, 1.0 - max(0.0, wind - 25.0) / 37.0)
        sea_state = min(wave_ok, wind_ok)

        score = self.lambda_param * sst_suitability + (1 - self.lambda_param) * sea_state

        if score >= 0.75:
            band, recommendation = "high", "Recommended fishing zone."
        elif score >= 0.45:
            band, recommendation = "moderate", "Workable, but conditions are not optimal."
        else:
            band, recommendation = "low", "Not recommended at present."

        return {
            "pfz_score": round(float(score), 4),
            "band": band,
            "recommendation": recommendation,
            "components": {
                "sst_suitability": round(sst_suitability, 4),
                "sea_state_suitability": round(sea_state, 4),
            },
            "raw": {"sst_c": sst, "wave_height_m": wave, "wind_speed_kmh": wind},
            "observed_at": obs.get("observed_at"),
            "live": True,
            "source": ", ".join(obs.get("sources", [])),
        }
