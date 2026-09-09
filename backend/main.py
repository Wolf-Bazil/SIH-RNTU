import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from backend.services.ask_service import router as ask_router

load_dotenv()

app = FastAPI(title="SIH_RNTU Disaster Resilience Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ask_router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
