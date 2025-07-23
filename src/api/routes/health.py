"""
Health check endpoints
"""

from datetime import datetime, timezone

# Import Agent type for proper type hints
from agno.agent import Agent
from fastapi import APIRouter, Depends, HTTPException, status

health_router = APIRouter(tags=["Health"])


# Dependency injection for agent
async def get_agent() -> Agent:
    """Get agent instance for health check"""
    from api.routes import fpt_agent

    if fpt_agent is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized",
        )
    return fpt_agent


@health_router.get("/health")
async def health_check(agent: Agent = Depends(get_agent)):
    """
    Health check endpoint

    Returns:
        Health status of the API and its components
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc),
        "components": {
            "api": {"status": "healthy"},
            "intent_detection": {"status": "healthy"},
            "agno_agent": {
                "status": "healthy" if agent is not None else "unavailable",
                "memory_available": hasattr(agent, "memory")
                and agent.memory is not None
                if agent
                else False,
                "storage_available": hasattr(agent, "storage")
                and agent.storage is not None
                if agent
                else False,
            },
        },
    }
