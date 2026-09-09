import os
import logging
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
from backend.agents.dispatcher import DispatcherAgent
from backend.services.ocean_data import fetch_observations

import re
from dotenv import load_dotenv

# Ensure environment variables are loaded. In containers the values arrive
# through the process environment (env_file), and load_dotenv never overrides
# those. env.txt is a duplicate of .env and is deliberately not read.
load_dotenv('.env')

logger = logging.getLogger("orca.ask")
router = APIRouter()
dispatcher = DispatcherAgent()

async def fetch_hyperlocal_telemetry(query: str):
    """
    Fetches real-time geocoding and meteorological data for any Indian town or district.
    Covers tier-1, tier-2, tier-3 cities, and rural tehsils across India.
    """
    try:
        # Strip common phrasing: e.g. "weather in jamui" -> "jamui"
        clean = re.sub(r'(?i)\b(weather|climate|forecast|rain|cyclone|risk|status|of|in|near|at)\b', '', query).strip()
        if not clean:
            clean = query.strip()

        async with httpx.AsyncClient(timeout=4.0) as client:
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={clean}&count=1&language=en&format=json"
            geo_res = await client.get(geo_url)
            if geo_res.status_code == 200:
                results = geo_res.json().get("results")
                if results:
                    loc = results[0]
                    lat = loc.get("latitude")
                    lon = loc.get("longitude")
                    name = loc.get("name")
                    state = loc.get("admin1", "India")
                    
                    # Fetch current weather
                    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation"
                    w_res = await client.get(w_url)
                    cur = w_res.json().get("current", {}) if w_res.status_code == 200 else {}
                    
                    return {
                        "found": True,
                        "city": name,
                        "state": state,
                        "lat": lat,
                        "lon": lon,
                        "temp": cur.get("temperature_2m"),
                        "humidity": cur.get("relative_humidity_2m"),
                        "wind": cur.get("wind_speed_10m"),
                        "rain": cur.get("precipitation")
                    }
    except Exception as e:
        logger.warning(f"Hyperlocal geocoding error: {e}")
    return {"found": False}

class AskRequest(BaseModel):
    question: Optional[str] = None
    language: Optional[str] = "en"
    agent: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    # The station the user is currently looking at. Used when the question
    # names no place, so the advisory describes the same water the dashboard
    # is showing instead of a fixed default point.
    lat: Optional[float] = None
    lon: Optional[float] = None

@router.post("/ask")
async def ask_endpoint(req: AskRequest):
    try:
        if req.agent:
            result = await dispatcher.process({
                "agent": req.agent,
                "data": req.data or {}
            })
            return {"agent": req.agent, "result": result, "answer": str(result)}

        question = req.question or "Current oceanic risk advisory"
        lang = req.language or "en"

        # 1. Resolve the place first, so the agents report on the location the
        #    user actually asked about rather than a fixed default point.
        city_info = await fetch_hyperlocal_telemetry(question)

        if city_info.get("found"):
            obs = await fetch_observations(city_info["lat"], city_info["lon"])
        elif req.lat is not None and req.lon is not None:
            obs = await fetch_observations(req.lat, req.lon)
        else:
            obs = await fetch_observations()

        # 2. Run the agents on that single shared observation.
        agent_input = {"observations": obs}
        sat_data = await dispatcher.process({"agent": "satellite_eo", "data": agent_input})
        met_data = await dispatcher.process({"agent": "met_sentinel", "data": agent_input})
        hazard_data = await dispatcher.process({"agent": "hazard_forecaster", "data": agent_input})

        mean_h = sat_data.get("result", {}).get("mean_hazard")
        ci_pfz = met_data.get("result", {}).get("mean_ci_pfz")
        trend = hazard_data.get("result", {}).get("trend", "unknown")

        loc_context = ""
        if city_info.get("found"):
            loc_context = (
                f"Location identified: {city_info['city']}, {city_info['state']} (Coords: {city_info['lat']}°N, {city_info['lon']}°E).\n"
                f"Local Observations: Temperature {city_info['temp']}°C, Humidity {city_info['humidity']}%, "
                f"Surface Wind {city_info['wind']} km/h, Precipitation {city_info['rain']} mm.\n"
            )
        elif req.lat is not None and req.lon is not None:
            # No place named, so say plainly which water this describes rather
            # than leaving the model to guess at a district.
            loc_context = (
                f"No place name was given. These readings are for the monitored "
                f"offshore point at {req.lat}°N, {req.lon}°E in the Indian EEZ.\n"
            )

        if obs.get("live"):
            sea_bits = []
            if obs.get("sst") is not None:
                sea_bits.append(f"SST {obs['sst']:.1f}°C")
            if obs.get("wave_height") is not None:
                sea_bits.append(f"significant wave height {obs['wave_height']:.1f} m")
            if obs.get("wave_period") is not None:
                sea_bits.append(f"wave period {obs['wave_period']:.0f} s")
            if obs.get("pressure") is not None:
                sea_bits.append(f"MSL pressure {obs['pressure']:.0f} hPa")
            if obs.get("wind_gusts") is not None:
                sea_bits.append(f"gusts {obs['wind_gusts']:.0f} km/h")

            indices = []
            if mean_h is not None:
                indices.append(f"Mean Hazard Index H(x,y,t)={mean_h:.3f}")
            if ci_pfz is not None:
                indices.append(f"Critical Index CI_PFZ={ci_pfz:.3f}")
            indices.append(f"Forecast Trend={trend}")

            outlook = hazard_data.get("result", {}).get("next_24h") or {}
            outlook_text = ""
            if outlook:
                outlook_text = (
                    f"\n24h outlook: peak rainfall {outlook.get('peak_precipitation_mm')} mm/h, "
                    f"peak wind {outlook.get('peak_wind_kmh')} km/h."
                )

            telemetry_summary = (
                f"{loc_context}"
                f"Sea state ({', '.join(obs.get('sources', []))}, observed {obs.get('observed_at')} UTC): "
                f"{', '.join(sea_bits)}.\n"
                f"Derived indices: {', '.join(indices)}.{outlook_text}"
            )
        else:
            telemetry_summary = (
                f"{loc_context}"
                "Sea state: live marine feed unavailable for this request; "
                "no oceanic indices were computed."
            )

        api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepinfra.com/v1/openai")

        # 3. Call DeepSeek V4 Pro
        if api_key and not api_key.startswith("sk-..."):
            try:
                system_prompt = (
                    "You are ORCA, the Oceanic Risk and Cyclone Advisory AI for SIH 2026 PS 176. "
                    "Provide a detailed, well-structured report in simple, plain language that anyone can easily understand. "
                    "Format your response with these exact markdown sections:\n"
                    "📍 Location Context (District, State, and whether inland or coastal)\n"
                    "🌤️ Current Weather (Temperature, Rain, Wind in simple everyday terms)\n"
                    "🌊 Oceanic & Cyclone Risk (Clear explanation of any cyclone, storm, or surge risk)\n"
                    "🛡️ Simple Safety Advisory (Practical, straightforward advice for local citizens, farmers, or fishermen)\n\n"
                    "Ground every statement in the telemetry you are given. Do not invent "
                    "measurements, cyclone names, or warnings that the telemetry does not "
                    "support. If the telemetry says a feed was unavailable, say so plainly "
                    "rather than estimating. If all readings are within normal limits, say "
                    "conditions are normal instead of manufacturing a risk.\n\n"
                    f"IMPORTANT: Respond completely in the requested language code: '{lang}' (e.g. if 'hi' use natural Hindi, if 'ta' Tamil, if 'bn' Bengali, if 'en' English)."
                )

                async with httpx.AsyncClient(timeout=12.0) as client:
                    resp = await client.post(
                        f"{base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={
                            "model": "deepseek-ai/DeepSeek-V4-Pro",
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Telemetry Data:\n{telemetry_summary}\n\nUser Question: {question}"}
                            ],
                            "max_tokens": 350
                        }
                    )
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"]
                        return {
                            "answer": content,
                            "telemetry": telemetry_summary,
                            "location": city_info,
                            "live": obs.get("live", False),
                            "observed_at": obs.get("observed_at"),
                            "sources": obs.get("sources", []),
                        }
            except Exception as llm_err:
                logger.warning(f"LLM request error: {llm_err}")

        # Structured deterministic fallback, used when no LLM key is set or the
        # LLM call fails. Every line below is derived from the readings; it
        # never asserts that conditions are safe without checking them.
        if city_info.get("found"):
            target_city = f"{city_info['city']}, {city_info['state']}"
            weather_desc = (
                f"Temperature is {city_info['temp']}°C with wind speed at "
                f"{city_info['wind']} km/h and humidity of {city_info['humidity']}%."
            )
        else:
            target_city = question
            weather_desc = "No matching place was found, so no local weather was retrieved."

        risk_lines = []
        advisory_lines = []

        if obs.get("live"):
            if mean_h is not None:
                risk_lines.append(f"- **Hazard Index H(x,y,t):** {mean_h:.2f} (trend: {trend})")
            if ci_pfz is not None:
                risk_lines.append(f"- **Critical Index CI_PFZ:** {ci_pfz:.2f}")
            if obs.get("sst") is not None:
                risk_lines.append(f"- **Sea surface temperature:** {obs['sst']:.1f} °C")
            if obs.get("wave_height") is not None:
                risk_lines.append(f"- **Significant wave height:** {obs['wave_height']:.1f} m")
            if obs.get("pressure") is not None:
                risk_lines.append(f"- **Mean sea level pressure:** {obs['pressure']:.0f} hPa")

            wave = obs.get("wave_height")
            wind = obs.get("wind_speed")
            rain = obs.get("precipitation")

            if wave is not None and wave >= 3.0:
                advisory_lines.append(
                    f"- Waves are running {wave:.1f} m. Do not put out to sea; "
                    f"this is above the INCOIS high wave warning level.")
            elif wave is not None and wave >= 2.0:
                advisory_lines.append(
                    f"- Waves are {wave:.1f} m. Small and artisanal craft should stay ashore.")

            if wind is not None and wind >= 62:
                advisory_lines.append(
                    f"- Wind is {wind:.0f} km/h, cyclonic storm strength. Follow local "
                    f"evacuation instructions.")
            elif wind is not None and wind >= 40:
                advisory_lines.append(f"- Wind is {wind:.0f} km/h. Secure loose structures.")

            if rain is not None and rain >= 7.5:
                advisory_lines.append(
                    f"- Rainfall is {rain:.1f} mm/h, heavy. Expect local waterlogging.")

            if not advisory_lines:
                advisory_lines.append(
                    "- All measured values are within normal limits. No warning is in force "
                    "for this location right now.")
            advisory_lines.append(
                f"- Readings observed {obs.get('observed_at')} UTC via "
                f"{', '.join(obs.get('sources', []))}.")
        else:
            risk_lines.append("- Live marine data could not be retrieved for this request.")
            advisory_lines.append(
                "- No advisory can be issued without data. Check IMD and INCOIS bulletins directly.")

        ans = (
            f"### 📍 Location Context\n"
            f"**Area:** {target_city}\n\n"
            f"### 🌤️ Current Weather\n"
            f"- {weather_desc}\n\n"
            f"### 🌊 Oceanic & Cyclone Risk\n"
            + "\n".join(risk_lines) + "\n\n"
            f"### 🛡️ Simple Safety Advisory\n"
            + "\n".join(advisory_lines)
        )

        return {
            "answer": ans,
            "telemetry": telemetry_summary,
            "location": city_info,
            "live": obs.get("live", False),
            "observed_at": obs.get("observed_at"),
            "sources": obs.get("sources", []),
        }

    except Exception as e:
        # Do not report a healthy-looking advisory when the pipeline failed —
        # a fake "hazard level nominal" reply is worse than an explicit error.
        logger.exception("Error in ask_endpoint")
        raise HTTPException(
            status_code=503,
            detail="ORCA advisory pipeline is temporarily unavailable."
        ) from e
