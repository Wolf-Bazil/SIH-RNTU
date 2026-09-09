import os
import json
import time
import uuid
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from backend.services.ask_service import router as ask_router, dispatcher

load_dotenv()

app = FastAPI(title="ORCA – Oceanic Risk & Cyclone Advisory System", version="1.0.0")

# Browsers reject `Access-Control-Allow-Origin: *` together with credentials, so
# the wildcard and credentials cannot both be enabled. Set CORS_ORIGINS to a
# comma-separated allowlist (e.g. "https://orca.example.com") in production.
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

@app.get("/api/alerts/stream")
async def stream_alerts(request: Request):
    """Server-Sent Events (SSE) stream for live maritime alerts and warnings."""
    async def event_generator():
        mock_scenarios = [
            {
                "type": "Cyclone Warning",
                "severity": "high",
                "message": "Depression detected in Bay of Bengal. Convective cloud tops < -72°C. Wind speed 48 knots.",
                "lat": 13.8,
                "lng": 83.5
            },
            {
                "type": "PFZ Advisory",
                "severity": "medium",
                "message": "Potential Fishing Zone (CI_PFZ: 0.84) identified off Nagapattinam. Optimal chlorophyll front.",
                "lat": 10.76,
                "lng": 79.84
            },
            {
                "type": "Swell Surge Alert",
                "severity": "medium",
                "message": "INCOIS High Wave Alert: 2.8m - 3.5m rough swells approaching Andhra Pradesh coastline.",
                "lat": 16.3,
                "lng": 81.8
            },
            {
                "type": "Eco-Route Optimization",
                "severity": "low",
                "message": "Modified A* J_route updated: -17.4% fuel burn achieved using prevailing surface currents.",
                "lat": 11.9,
                "lng": 80.6
            },
            {
                "type": "IMBL Boundary Clearance",
                "severity": "low",
                "message": "Boundary Monitor: All active tracked artisanal vessels verified safely inside Indian EEZ.",
                "lat": 9.28,
                "lng": 79.31
            }
        ]
        seq = 0
        while True:
            if await request.is_disconnected():
                break
            # Pick scenario and add dynamic timestamp + id
            alert = mock_scenarios[seq % len(mock_scenarios)].copy()
            alert["id"] = str(uuid.uuid4())
            alert["timestamp"] = time.strftime("%H:%M:%S UTC")
            
            payload = json.dumps(alert)
            yield f"event: alert\ndata: {payload}\n\n"
            seq += 1
            await asyncio.sleep(4)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/api/overlays")
async def get_overlays():
    """Returns spatial overlay telemetry from active agent engines.

    The agents are chained: the satellite grid feeds the PFZ reasoner and the
    forecaster, which previously received empty input and returned nothing.
    Only summary scalars are returned; the raw 100x100 grids stay server-side
    so the response is a few hundred bytes instead of several megabytes.
    """
    sat = (await dispatcher.process({"agent": "satellite_eo", "data": {}})).get("result", {})
    met = (await dispatcher.process({"agent": "met_sentinel", "data": {}})).get("result", {})

    pfz = (await dispatcher.process({
        "agent": "pfz_reasoner",
        "data": {"hazard_index": sat.get("hazard_index", []), "ci_pfz": met.get("ci_pfz", [])}
    })).get("result", {})

    hazard = (await dispatcher.process({
        "agent": "hazard_forecaster",
        "data": {"hazard_index": sat.get("hazard_index", [])}
    })).get("result", {})

    route = (await dispatcher.process({"agent": "eco_route_planner", "data": {}})).get("result", {})

    return {
        "satellite": {
            "mean_hazard": sat.get("mean_hazard"),
            "max_hazard": sat.get("max_hazard"),
            "min_hazard": sat.get("min_hazard"),
        },
        "met": {
            "mean_ci_pfz": met.get("mean_ci_pfz"),
            "max_ci_pfz": met.get("max_ci_pfz"),
        },
        "pfz": {
            "flood_zone_percentage": pfz.get("flood_zone_percentage"),
        },
        "hazard": {
            "mean_forecast": hazard.get("mean_forecast"),
            "trend": hazard.get("trend"),
        },
        "eco_route": {
            "path": route.get("path", []),
            "path_length": route.get("path_length"),
            "total_cost_J_route": route.get("total_cost_J_route"),
            "found": route.get("found"),
        },
    }
