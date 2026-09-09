from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
from backend.agents.dispatcher import DispatcherAgent

router = APIRouter()
dispatcher = DispatcherAgent()

class AskRequest(BaseModel):
    agent: str
    data: Optional[Dict[str, Any]] = {}

class AskResponse(BaseModel):
    agent: str
    result: Dict[str, Any]

@router.post("/ask", response_model=AskResponse)
async def ask_agent(request: AskRequest):
    try:
        result = await dispatcher.process({
            "agent": request.agent,
            "data": request.data
        })
        return AskResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
