from typing import Any, Dict

import numpy as np

from backend.agents.base_agent import BaseAgent
from backend.services.ocean_data import fetch_observations


class HazardForecasterAgent(BaseAgent):
    """Projects hazard evolution from the live hourly forecast.

    The gridded path still applies exponential smoothing,
    H(t+1) = H(t) + eta * (H(t) - H(t-1)), when a caller supplies
    ``hazard_index``.

    Without a grid the agent uses the real 24h hourly precipitation and wind
    series from Open-Meteo and compares the next 6 hours against the following
    18, which yields a trend grounded in an actual forecast rather than in the
    previous placeholder, where H_previous defaulted to H_current and the
    trend was therefore constant by construction.
    """

    def __init__(self, eta: float = 0.3):
        super().__init__("HazardForecaster")
        self.eta = eta

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Forecasting hazard evolution")

        supplied = input_data.get("hazard_index")
        if supplied:
            H_current = np.array(supplied)
            H_previous = np.array(input_data.get("hazard_previous", H_current))
            H_forecast = H_current + self.eta * (H_current - H_previous)

            mean_forecast = float(np.mean(H_forecast))
            mean_current = float(np.mean(H_current))
            delta = mean_forecast - mean_current
            if abs(delta) < 1e-9:
                trend = "stable"
            else:
                trend = "increasing" if delta > 0 else "decreasing"

            return {
                "forecast": H_forecast.tolist(),
                "mean_forecast": mean_forecast,
                "trend": trend,
                "live": False,
                "source": "caller-supplied grid",
            }

        obs = input_data.get("observations")
        if obs is None:
            lat = input_data.get("lat")
            lon = input_data.get("lon")
            obs = await (fetch_observations(lat, lon)
                         if lat is not None and lon is not None
                         else fetch_observations())

        rain = obs.get("precipitation_forecast") or []
        wind = obs.get("wind_forecast") or []

        if not obs.get("live") or len(rain) < 12 or len(wind) < 12:
            return {
                "forecast": [],
                "mean_forecast": None,
                "trend": "unknown",
                "live": False,
                "source": "unavailable",
                "detail": "no hourly forecast series available",
            }

        def _window_mean(series, start, end):
            window = series[start:end]
            return float(np.mean(window)) if window else 0.0

        # Near term is the next 6 hours, later is the rest of the 24h horizon.
        near_rain, later_rain = _window_mean(rain, 0, 6), _window_mean(rain, 6, 24)
        near_wind, later_wind = _window_mean(wind, 0, 6), _window_mean(wind, 6, 24)

        # Scale each change by the bound used in derive_drivers so rain and
        # wind contribute on comparable footing.
        rain_delta = (later_rain - near_rain) / 25.0
        wind_delta = (later_wind - near_wind) / 120.0
        delta = 0.5 * rain_delta + 0.5 * wind_delta

        # 2% of the normalised range: below this the forecast is flat within
        # the model's own resolution.
        if abs(delta) < 0.02:
            trend = "stable"
        else:
            trend = "increasing" if delta > 0 else "decreasing"

        return {
            "trend": trend,
            "delta": round(float(delta), 4),
            "next_6h": {
                "mean_precipitation_mm": round(near_rain, 2),
                "mean_wind_kmh": round(near_wind, 1),
            },
            "next_24h": {
                "mean_precipitation_mm": round(later_rain, 2),
                "mean_wind_kmh": round(later_wind, 1),
                "peak_precipitation_mm": round(float(np.max(rain)), 2),
                "peak_wind_kmh": round(float(np.max(wind)), 1),
            },
            "observed_at": obs.get("observed_at"),
            "live": True,
            "source": ", ".join(obs.get("sources", [])),
        }
