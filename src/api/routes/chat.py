"""
Chat API endpoints for FPT University Agent
Optimized for Agno framework best practices
"""

import json
import logging
import dataclasses
from dataclasses import asdict
from typing import AsyncIterator, Optional

# Import Agent type for proper type hints
from agno.agent import Agent
from agno.memory.v2.memory import Memory  # Import Memory v2 for type checking
from agno.run.response import RunResponse, RunResponseEvent
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from api.factories.service_factory import ServiceFactory

# Configure logging
logger = logging.getLogger(__name__)

chat_router = APIRouter(prefix="/chat", tags=["Chat"])


# Core Pydantic models
class ChatRequest(BaseModel):
    """Chat request with validation"""

    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    user_id: str = Field(
        ..., min_length=1, max_length=100, description="Unique user identifier"
    )
    session_id: Optional[str] = Field(
        None,
        max_length=100,
        description="Session identifier for conversation continuity",
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


# Dependency injection
def get_service_factory(request: Request) -> ServiceFactory:
    """Get service factory from app state"""
    service_factory = request.app.state.service_factory
    if not service_factory:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Services not initialized",
        )
    return service_factory


def get_agent_for_chat(
    chat_request: ChatRequest,
    service_factory: ServiceFactory = Depends(get_service_factory),
) -> Agent:
    """Get a new agent instance for each chat request."""
    return service_factory.get_fpt_agent(
        user_id=chat_request.user_id, session_id=chat_request.session_id
    )


def get_agent_for_user(
    user_id: str, service_factory: ServiceFactory = Depends(get_service_factory)
) -> Agent:
    """Get a temporary agent to access user-specific data (memory)."""
    return service_factory.get_fpt_agent(user_id=user_id)


def get_agent_for_session(
    session_id: str, service_factory: ServiceFactory = Depends(get_service_factory)
) -> Agent:
    """Get a temporary agent to access session-specific data (history)."""
    return service_factory.get_fpt_agent(session_id=session_id)


# API Endpoints
@chat_router.post("/send")
async def send_message(
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    agent: Agent = Depends(get_agent_for_chat),
):
    """Send a message to the FPT University Agent"""
    logger.info(
        f"Processing message for user {agent.user_id}, session {agent.session_id}"
    )

    response: RunResponse = await agent.arun(
        chat_request.message,
        # user_id and session_id are now in the agent's context
        stream=False,
    )

    logger.info(f"Successfully processed message for user {agent.user_id}")

    # Automatically rename the session in the background
    background_tasks.add_task(agent.auto_rename_session)

    return response.content


@chat_router.post("/stream")
async def stream_message(
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    agent: Agent = Depends(get_agent_for_chat),
):
    """Stream a message using Agno's built-in streaming with tool calls"""

    async def generate_stream():
        """Generate Server-Sent Events stream using Agno's built-in streaming"""
        response_stream: AsyncIterator[RunResponseEvent] = await agent.arun(
            chat_request.message,
            # user_id and session_id are now in the agent's context
            stream=True,
            stream_intermediate_steps=True,
        )

        async for event in response_stream:
            event_dict = event.to_dict()
            yield f"data: {json.dumps(event_dict, default=str)}\n\n"

    # Automatically rename the session in the background after the stream completes
    background_tasks.add_task(agent.auto_rename_session)

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@chat_router.get("/memory/{user_id}")
async def get_user_memories(agent: Agent = Depends(get_agent_for_user)):
    """Get user memories from the agent's memory system using Agno standard method"""
    if not isinstance(agent.memory, Memory):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Memory system not available or is not V2",
        )

    memories = agent.memory.get_user_memories(user_id=agent.user_id)
    serializable_memories = [asdict(memory) for memory in memories] if memories else []

    return {
        "memories": serializable_memories,
        "count": len(serializable_memories),
        "user_id": agent.user_id,
    }


@chat_router.delete("/memory/{user_id}")
async def clear_user_memories(agent: Agent = Depends(get_agent_for_user)):
    """Clear all memories for a specific user using standard Agno method"""
    if not isinstance(agent.memory, Memory):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Memory system not available or is not V2",
        )

    user_memories = agent.memory.get_user_memories(user_id=agent.user_id)
    if user_memories:
        for memory in user_memories:
            if hasattr(memory, "memory_id") and memory.memory_id is not None:
                agent.memory.delete_user_memory(
                    user_id=agent.user_id, memory_id=memory.memory_id
                )

    return {"message": f"Memories cleared for user {agent.user_id}"}


@chat_router.get("/sessions/{user_id}")
async def get_user_sessions(agent: Agent = Depends(get_agent_for_user)):
    """Get all session IDs for a specific user using Agno standard method"""
    if not hasattr(agent, "storage") or agent.storage is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Storage system not available",
        )

    sessions = agent.storage.get_all_session_ids(agent.user_id)

    return {"sessions": sessions, "count": len(sessions), "user_id": agent.user_id}


@chat_router.get("/history/{session_id}")
async def get_session_history(agent: Agent = Depends(get_agent_for_session)):
    """Get conversation history for a specific session using Agno standard method"""
    messages = agent.get_messages_for_session(session_id=agent.session_id)
    serializable_messages = [
        msg.model_dump(include={"role", "content", "timestamp", "created_at"})
        for msg in messages
    ]

    return {
        "history": serializable_messages,
        "session_id": agent.session_id,
        "count": len(serializable_messages),
    }
