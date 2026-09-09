import asyncio
import json
import os
import time
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.services.alerting import MONITORED_STATIONS, evaluate_station
from backend.services.ask_service import dispatcher
from backend.services.ask_service import router as ask_router
from backend.services.ocean_data import fetch_observations

load_dotenv()

app = FastAPI(title="ORCA – Oceanic Risk & Cyclone Advisory System", version="1.0.0")

# Browsers reject `Access-Control-Allow-Origin: *` together with credentials, so
# the wildcard and credentials cannot both be enabled. Set CORS_ORIGINS to a
# comma-separated allowlist (e.g. "https://orca.eteon.net") in production.
_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_credentials=bool(_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ask_router, prefix="/api")


@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "platform": "ORCA", "ps": "SIH 2026 PS 176"}


@app.get("/api/stations")
async def list_stations():
    """The coastal points the alert stream monitors."""
    return {"stations": MONITORED_STATIONS}


@app.get("/api/alerts/stream")
async def stream_alerts(request: Request):
    """Live maritime alerts over Server-Sent Events.

    Each event is produced by evaluating real observations for one monitored
    station against published thresholds. The stream rotates through the
    stations so every one is refreshed in turn; ocean_data caches upstream
    responses for 10 minutes, matching the 15-minute upstream update interval,
    so the rotation does not generate a request per event.
    """
    async def event_generator():
        index = 0
        while True:
            if await request.is_disconnected():
                break

            station = MONITORED_STATIONS[index % len(MONITORED_STATIONS)]
            index += 1

            try:
                obs = await fetch_observations(station["lat"], station["lon"])
                alert = evaluate_station(station, obs)
            except Exception:
                alert = None

            if alert:
                alert["id"] = str(uuid.uuid4())
                alert["timestamp"] = time.strftime("%H:%M:%S UTC", time.gmtime())
                yield f"event: alert\ndata: {json.dumps(alert)}\n\n"
            else:
                # Comment frame: keeps the connection and any intermediary
                # proxy alive without fabricating an alert.
                yield ": keep-alive\n\n"

            await asyncio.sleep(4)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/overlays")
async def get_overlays(lat: float | None = None, lon: float | None = None):
    """Spatial overlay telemetry from the agent engines, on live observations.

    One observation is fetched and shared by every agent, so a request makes at
    most two upstream calls rather than one per agent. Only summary scalars are
    returned; raw series stay server-side.
    """
    obs = await (fetch_observations(lat, lon)
                 if lat is not None and lon is not None
                 else fetch_observations())

    sat = (await dispatcher.process(
        {"agent": "satellite_eo", "data": {"observations": obs}})).get("result", {})
    met = (await dispatcher.process(
        {"agent": "met_sentinel", "data": {"observations": obs}})).get("result", {})
    hazard = (await dispatcher.process(
        {"agent": "hazard_forecaster", "data": {"observations": obs}})).get("result", {})
    pfz = (await dispatcher.process(
        {"agent": "pfz_reasoner", "data": {"observations": obs}})).get("result", {})
    route = (await dispatcher.process(
        {"agent": "eco_route_planner",
         "data": {"mean_hazard": sat.get("mean_hazard")}})).get("result", {})

    # Attribute the hazard index to its drivers using the weights that actually
    # produced it, so the UI can show why the number is what it is.
    xai = (await dispatcher.process({
        "agent": "xai_auditor",
        "data": {
            "index": "Hazard Index H(x,y,t)",
            "score": sat.get("mean_hazard"),
            "components": sat.get("components"),
            "weights": {"sst": 0.4, "wind": 0.3, "precipitation": 0.3},
            "observed_at": obs.get("observed_at"),
        },
    })).get("result", {})

    return {
        "live": obs.get("live", False),
        "observed_at": obs.get("observed_at"),
        "sources": obs.get("sources", []),
        "location": {"lat": obs.get("lat"), "lon": obs.get("lon")},
        "conditions": {
            "sst_c": obs.get("sst"),
            "wave_height_m": obs.get("wave_height"),
            "wave_period_s": obs.get("wave_period"),
            "wave_direction_deg": obs.get("wave_direction"),
            "wind_speed_kmh": obs.get("wind_speed"),
            "wind_gusts_kmh": obs.get("wind_gusts"),
            "pressure_hpa": obs.get("pressure"),
            "precipitation_mm": obs.get("precipitation"),
        },
        "satellite": {
            "mean_hazard": sat.get("mean_hazard"),
            "components": sat.get("components"),
        },
        "met": {
            "mean_ci_pfz": met.get("mean_ci_pfz"),
            "components": met.get("components"),
        },
        "hazard": {
            "trend": hazard.get("trend"),
            "delta": hazard.get("delta"),
            "next_6h": hazard.get("next_6h"),
            "next_24h": hazard.get("next_24h"),
        },
        "pfz": {
            "score": pfz.get("pfz_score"),
            "band": pfz.get("band"),
            "recommendation": pfz.get("recommendation"),
            "components": pfz.get("components"),
        },
        "explanation": xai.get("explanation"),
        # The eco-route planner still runs the modified A* over a synthetic
        # environmental grid; no live routing cost surface is wired yet.
        "eco_route": {
            "path": route.get("path", []),
            "path_length": route.get("path_length"),
            "total_cost_J_route": route.get("total_cost_J_route"),
            "found": route.get("found"),
            "environmental_field": route.get("environmental_field"),
            "live": False,
        },
    }
