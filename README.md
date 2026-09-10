# SIH_RNTU – AI‑Driven Disaster Resilience Platform

## Overview
SIH_RNTU is a multi‑agent system that integrates satellite Earth observation, meteorological data, and AI reasoning to provide real‑time hazard forecasting, boundary monitoring, and eco‑friendly route planning. The platform supports multilingual interaction and explainable AI (XAI) outputs.

## Key Features
- **Satellite EO Agent** – processes optical/SAR imagery to compute hazard index H(x,y,t)
- **Met‑Sentinel Agent** – ingests weather forecasts and computes CI_PFZ (Critical Index for Potential Flood Zones)
- **PFZ Reasoner** – combines H and CI_PFZ to delineate potential flood zones
- **Hazard Forecaster** – predicts hazard evolution over time
- **Boundary Monitor** – tracks administrative boundaries and alerts on encroachment
- **Eco‑Route Planner** – computes optimal routes using a modified A* algorithm (J_route)
- **Multilingual Agent** – translates queries and responses
- **XAI Auditor** – provides explanations for AI decisions
- **Dispatcher** – orchestrates agent workflows

## Tech Stack
- **Backend**: FastAPI, Python 3.11, LangChain, Redis
- **Frontend**: React, Vite, Tailwind CSS, Leaflet
- **Infrastructure**: Docker, Nginx

## Getting Started
1. Clone the repository
2. Copy `backend/.env.example` to `backend/.env` and fill in required keys
3. Run `docker-compose up --build`
4. Access the frontend at `http://localhost:3000`

### Place lookup

Questions are resolved against a local gazetteer of every Indian state,
district, sub-district, town and village, built from the GeoNames India dump
(CC BY 4.0). The Docker build produces it; to build it for a local backend run:

```bash
python backend/data/build_gazetteer.py
```

That writes `backend/data/india_places.sqlite3` (~57 MB, ~566k places, about
half a minute). The file is generated, not tracked. Without it the backend
falls back to the upstream geocoder, which is worldwide and fuzzy — it answers
"goa" with Genoa, Italy — so ORCA is noticeably worse at Indian places until it
is built.

## Project Structure
