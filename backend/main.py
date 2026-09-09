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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
    """Returns spatial overlay telemetry from active agent engines."""
    sat = await dispatcher.process({"agent": "satellite_eo", "data": {}})
    pfz = await dispatcher.process({"agent": "pfz_reasoner", "data": {}})
    hazard = await dispatcher.process({"agent": "hazard_forecaster", "data": {}})
    route = await dispatcher.process({"agent": "eco_route_planner", "data": {}})
    
    return {
        "satellite": sat.get("result", {}),
        "pfz": pfz.get("result", {}),
        "hazard": hazard.get("result", {}),
        "eco_route": route.get("result", {})
    }
