"""
Health check endpoints
"""

from fastapi import APIRouter, status, Depends
from pydantic import BaseModel
from datetime import datetime, timezone

# Import Agent type for proper type hints
from agno.agent import Agent

health_router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    version: str
    timestamp: datetime
    components: dict


# Dependency injection for agent
async def get_agent() -> Agent:
    """Get agent instance for health check"""
    from api.routes import fpt_agent
    return fpt_agent


@health_router.get("/health", response_model=HealthResponse)
async def health_check(agent: Agent = Depends(get_agent)):
    """
    Health check endpoint
    
    Returns:
        HealthResponse: Health status of the API and its components
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
        components={
            "api": {"status": "healthy"},
            "intent_detection": {"status": "healthy"},
            "agno_agent": {
                "status": "healthy" if agent is not None else "unavailable",
                "memory_available": hasattr(agent, 'memory') and agent.memory is not None if agent else False,
                "storage_available": hasattr(agent, 'storage') and agent.storage is not None if agent else False
            }
        }
    )

