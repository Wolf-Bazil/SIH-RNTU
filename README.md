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

## Project Structure
