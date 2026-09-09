"""Live observational data for the ORCA agents.

Replaces the ``np.random.random`` placeholders the agents used to run on.
Every value returned here comes from a real request made at call time.

Sources, both keyless and updated every 15 minutes:

* ``marine-api.open-meteo.com`` -- significant wave height, wave period, wave
  direction, sea surface temperature.
* ``api.open-meteo.com`` -- 2m temperature, mean sea level pressure, 10m wind,
  wind gusts, precipitation, plus the hourly forecast series.

Two sources configured in .env were evaluated and rejected:

* INCOIS ERDDAP is reachable and holds genuine Indian Ocean datasets, but a
  single tabledap query takes ~27s, far too slow to sit inside a user request.
  It suits a scheduled ingest, not this path.
* The configured CMEMS host ``api.marine.copernicus.eu`` does not resolve;
  Copernicus Marine requires their toolbox and a subscription workflow.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Tuple

import httpx

logger = logging.getLogger("orca.ocean_data")

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# Bay of Bengal, matching the frontend map's default centre.
DEFAULT_LAT = 14.0
DEFAULT_LON = 83.5

# The upstream data changes every 15 minutes, so a shorter TTL only adds
# latency and load without adding information.
_CACHE_TTL_SECONDS = 600

# A response missing one of its two sources is cached only briefly. Caching a
# partial reading for the full TTL let a single transient timeout blank the
# wind, pressure and rainfall panels for ten minutes, and left the hazard
# index resting on sea surface temperature alone.
_PARTIAL_CACHE_TTL_SECONDS = 45

_EXPECTED_SOURCES = 2
_cache: Dict[Tuple[float, float], Tuple[float, Dict[str, Any]]] = {}
_cache_lock = asyncio.Lock()


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _normalise(value: Optional[float], low: float, high: float,
               invert: bool = False) -> Optional[float]:
    """Scale a physical measurement onto [0, 1].

    ``low`` and ``high`` are the physically meaningful bounds for the Indian
    Ocean, documented at each call site. Returns None for a missing reading so
    callers can distinguish "no data" from "zero".
    """
    if value is None:
        return None
    scaled = (float(value) - low) / (high - low)
    return _clamp01(1.0 - scaled if invert else scaled)


async def fetch_observations(lat: float = DEFAULT_LAT,
                             lon: float = DEFAULT_LON) -> Dict[str, Any]:
    """Fetch live marine and atmospheric readings for one point.

    Returns a dict with a ``live`` flag. When ``live`` is False the upstream
    request failed and every reading is None -- agents then report that they
    are running without data rather than inventing numbers.
    """
    key = (round(lat, 2), round(lon, 2))

    async with _cache_lock:
        hit = _cache.get(key)
        if hit:
            age = time.time() - hit[0]
            complete = len(hit[1].get("sources", [])) >= _EXPECTED_SOURCES
            ttl = _CACHE_TTL_SECONDS if complete else _PARTIAL_CACHE_TTL_SECONDS
            if age < ttl:
                return hit[1]

    result: Dict[str, Any] = {
        "live": False,
        "complete": False,
        "lat": lat,
        "lon": lon,
        "observed_at": None,
        "sources": [],
        "wave_height": None,
        "wave_period": None,
        "wave_direction": None,
        "sst": None,
        "temperature": None,
        "pressure": None,
        "wind_speed": None,
        "wind_gusts": None,
        "precipitation": None,
        "precipitation_forecast": [],
        "wind_forecast": [],
    }

    marine_params = {
        "latitude": lat,
        "longitude": lon,
        "current": "wave_height,wave_period,wave_direction,sea_surface_temperature",
    }
    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,pressure_msl,wind_speed_10m,wind_gusts_10m,precipitation",
        "hourly": "precipitation,wind_speed_10m",
        "forecast_days": 2,
        "timezone": "UTC",
    }

    try:
        # 8s was too tight when the SSE rotation and a dashboard refresh
        # overlapped: one call would time out and the reading came back half
        # populated. One retry absorbs a transient upstream blip.
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(14.0, connect=6.0),
            transport=httpx.AsyncHTTPTransport(retries=1),
        ) as client:
            marine_res, weather_res = await asyncio.gather(
                client.get(MARINE_URL, params=marine_params),
                client.get(WEATHER_URL, params=weather_params),
                return_exceptions=True,
            )

        for label, res in (("marine", marine_res), ("weather", weather_res)):
            if isinstance(res, Exception):
                logger.warning("%s feed failed for %s,%s: %s", label, lat, lon, res)
            elif res.status_code != 200:
                logger.warning("%s feed returned %s for %s,%s",
                               label, res.status_code, lat, lon)

        if isinstance(marine_res, httpx.Response) and marine_res.status_code == 200:
            current = marine_res.json().get("current", {})
            result.update({
                "wave_height": current.get("wave_height"),
                "wave_period": current.get("wave_period"),
                "wave_direction": current.get("wave_direction"),
                "sst": current.get("sea_surface_temperature"),
                "observed_at": current.get("time"),
            })
            result["sources"].append("open-meteo-marine")

        if isinstance(weather_res, httpx.Response) and weather_res.status_code == 200:
            payload = weather_res.json()
            current = payload.get("current", {})
            hourly = payload.get("hourly", {})
            result.update({
                "temperature": current.get("temperature_2m"),
                "pressure": current.get("pressure_msl"),
                "wind_speed": current.get("wind_speed_10m"),
                "wind_gusts": current.get("wind_gusts_10m"),
                "precipitation": current.get("precipitation"),
                "precipitation_forecast": [
                    v for v in (hourly.get("precipitation") or [])[:24] if v is not None
                ],
                "wind_forecast": [
                    v for v in (hourly.get("wind_speed_10m") or [])[:24] if v is not None
                ],
            })
            result["observed_at"] = result["observed_at"] or current.get("time")
            result["sources"].append("open-meteo-forecast")

        result["live"] = bool(result["sources"])
        result["complete"] = len(result["sources"]) >= _EXPECTED_SOURCES
    except Exception:
        logger.warning("live observation fetch failed for %s,%s", lat, lon, exc_info=True)

    if result["live"]:
        async with _cache_lock:
            # A previous complete reading beats a fresh partial one: better to
            # serve values a few minutes old than to blank half the dashboard.
            previous = _cache.get(key)
            if (not result["complete"] and previous
                    and previous[1].get("complete")
                    and (time.time() - previous[0]) < _CACHE_TTL_SECONDS):
                return previous[1]
            _cache[key] = (time.time(), result)

    return result


def derive_drivers(obs: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """Turn raw readings into the normalised [0, 1] drivers the agents consume.

    Bounds are chosen from Indian Ocean cyclone climatology:

    * SST 24-32 C. Tropical cyclogenesis needs roughly 26.5 C, so warmer water
      means more available energy and a higher hazard contribution.
    * Wind 0-120 km/h. 62 km/h is cyclonic strength, 118 km/h severe.
    * Pressure 990-1013 hPa, inverted -- a deeper low is more hazardous.
    * Precipitation 0-25 mm/h, the rate at which coastal flooding starts.
    * Wave height 0-6 m. INCOIS issues high wave alerts from about 3 m.
    """
    return {
        "sst": _normalise(obs.get("sst"), 24.0, 32.0),
        "wind": _normalise(obs.get("wind_speed"), 0.0, 120.0),
        "gusts": _normalise(obs.get("wind_gusts"), 0.0, 150.0),
        "pressure_deficit": _normalise(obs.get("pressure"), 990.0, 1013.0, invert=True),
        "precipitation": _normalise(obs.get("precipitation"), 0.0, 25.0),
        "wave": _normalise(obs.get("wave_height"), 0.0, 6.0),
    }
