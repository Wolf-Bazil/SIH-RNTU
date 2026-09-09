"""Threshold evaluation that turns live readings into maritime alerts.

Replaces the hardcoded scenario list the SSE stream used to cycle through.
Every alert here is raised only because a real measurement crossed a published
threshold, and the measured value is quoted in the message.

Thresholds follow INCOIS and IMD operational practice:

* Wave height -- INCOIS issues high wave warnings from about 3 m; 2 m is the
  lower "rough sea" advisory used for artisanal craft.
* Wind -- IMD calls 62 km/h cyclonic storm strength and 88 km/h severe.
* Pressure -- 1000 hPa marks a well-defined low in this basin, 990 a deep one.
* Rainfall -- IMD classes 7.5 mm/h as heavy and 15 mm/h as very heavy.
* SST -- 28 C is the accepted threshold above which the ocean supports
  tropical cyclone intensification.
"""

from typing import Any, Dict, List, Optional, Tuple

# Points along the Indian coastline and the adjacent basins.
MONITORED_STATIONS: List[Dict[str, Any]] = [
    {"name": "Bay of Bengal (central)", "lat": 14.0, "lon": 86.0},
    {"name": "Off Nagapattinam", "lat": 10.76, "lon": 79.95},
    {"name": "Off Visakhapatnam", "lat": 17.70, "lon": 83.40},
    {"name": "Off Paradip", "lat": 20.26, "lon": 86.80},
    {"name": "Gulf of Mannar", "lat": 9.10, "lon": 79.30},
    {"name": "Arabian Sea (off Kochi)", "lat": 9.90, "lon": 75.90},
    {"name": "Off Mumbai", "lat": 18.90, "lon": 72.60},
    {"name": "Andaman Sea", "lat": 11.66, "lon": 92.50},
]


def evaluate_station(station: Dict[str, Any],
                     obs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return the most severe alert this station's readings justify, if any.

    Returns None when the fetch failed or when every reading is within normal
    limits -- the caller then emits a keep-alive rather than inventing an
    event.
    """
    if not obs.get("live"):
        return None

    wave = obs.get("wave_height")
    wind = obs.get("wind_speed")
    gusts = obs.get("wind_gusts")
    pressure = obs.get("pressure")
    rain = obs.get("precipitation")
    sst = obs.get("sst")
    period = obs.get("wave_period")

    # (severity, type, message)
    candidates: List[Tuple[str, str, str]] = []

    if wind is not None and wind >= 88:
        candidates.append(("high", "Severe Cyclonic Wind",
                           f"Sustained wind {wind:.0f} km/h at {station['name']} "
                           f"exceeds IMD severe cyclonic storm strength."))
    elif wind is not None and wind >= 62:
        candidates.append(("high", "Cyclonic Wind Warning",
                           f"Sustained wind {wind:.0f} km/h at {station['name']} "
                           f"has reached cyclonic storm strength."))
    elif gusts is not None and gusts >= 62:
        candidates.append(("medium", "Squall Advisory",
                           f"Gusts to {gusts:.0f} km/h recorded at {station['name']}."))

    if pressure is not None and pressure <= 990:
        candidates.append(("high", "Deep Low Pressure",
                           f"Mean sea level pressure {pressure:.0f} hPa at "
                           f"{station['name']} indicates a deep low."))
    elif pressure is not None and pressure <= 1000:
        candidates.append(("medium", "Low Pressure Area",
                           f"Pressure {pressure:.0f} hPa at {station['name']} "
                           f"indicates a well-marked low."))

    if wave is not None and wave >= 3.0:
        candidates.append(("high", "High Wave Alert",
                           f"Significant wave height {wave:.1f} m at "
                           f"{station['name']} is above the INCOIS warning level."))
    elif wave is not None and wave >= 2.0:
        detail = f" with a {period:.0f}s period" if period else ""
        candidates.append(("medium", "Rough Sea Advisory",
                           f"Waves running {wave:.1f} m{detail} at "
                           f"{station['name']}. Small craft should exercise caution."))

    if rain is not None and rain >= 15:
        candidates.append(("high", "Very Heavy Rainfall",
                           f"Rainfall {rain:.1f} mm/h at {station['name']}."))
    elif rain is not None and rain >= 7.5:
        candidates.append(("medium", "Heavy Rainfall",
                           f"Rainfall {rain:.1f} mm/h at {station['name']}."))

    # Calm water is checked before the SST anomaly. Indian Ocean SST sits above
    # 28 C across most of the basin for much of the year, so testing it first
    # would mask the more actionable "safe to sail" signal at every station.
    if not candidates and wave is not None and wave < 1.5 and (wind is None or wind < 25):
        calm = f"Calm sea at {station['name']}: waves {wave:.1f} m"
        calm += f", wind {wind:.0f} km/h" if wind is not None else ""
        calm += f", SST {sst:.1f} °C." if sst is not None else "."
        candidates.append(("low", "Favourable Fishing Conditions", calm))

    if not candidates and sst is not None and sst >= 28.0:
        candidates.append(("low", "Warm SST Anomaly",
                           f"Sea surface temperature {sst:.1f} °C at "
                           f"{station['name']} is above the 28 °C threshold that "
                           f"supports cyclone intensification."))

    if not candidates:
        return None

    rank = {"high": 0, "medium": 1, "low": 2}
    severity, alert_type, message = min(candidates, key=lambda c: rank[c[0]])

    return {
        "type": alert_type,
        "severity": severity,
        "message": message,
        "lat": station["lat"],
        "lng": station["lon"],
        "station": station["name"],
        "observed_at": obs.get("observed_at"),
        "readings": {
            "wave_height_m": wave,
            "wave_period_s": period,
            "wind_speed_kmh": wind,
            "wind_gusts_kmh": gusts,
            "pressure_hpa": pressure,
            "precipitation_mm": rain,
            "sst_c": sst,
        },
        "sources": obs.get("sources", []),
    }
