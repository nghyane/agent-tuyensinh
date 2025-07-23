"""
Chat API endpoints for FPT University Agent
Optimized for Agno framework best practices
"""

import json
import logging
from typing import Optional

# Import Agent type for proper type hints
from agno.agent import Agent
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

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
async def get_agent() -> Agent:
    """Get agent instance with proper error handling"""
    from api.routes import fpt_agent

    if fpt_agent is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized",
        )
    return fpt_agent


# Core chat functionality
async def _process_chat_message(
    agent: Agent, message: str, user_id: str, session_id: Optional[str] = None
):
    """Process chat message using Agno's built-in handling"""
    logger.info(f"Processing message for user {user_id}, session {session_id}")

    # Run agent with Agno's built-in error handling
    response = await agent.arun(message, user_id=user_id, session_id=session_id)

    logger.info(f"Successfully processed message for user {user_id}")
    return response


def _format_sse_data(data) -> str:
    """Format data as Server-Sent Events"""
    # Auto convert object to dict using vars()
    if hasattr(data, '__dict__'):
        event_dict = vars(data)
    else:
        event_dict = data
    
    return f"data: {json.dumps(event_dict, default=str)}\n\n"


# API Endpoints
@chat_router.post("/send")
async def send_message(chat_request: ChatRequest, agent: Agent = Depends(get_agent)):
    """Send a message to the FPT University Agent"""
    if not chat_request.session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required for conversation continuity",
        )

    # Use Agno's built-in response directly
    response = await _process_chat_message(
        agent=agent,
        message=chat_request.message,
        user_id=chat_request.user_id,
        session_id=chat_request.session_id,
    )

    return response


@chat_router.post("/stream")
async def stream_message(chat_request: ChatRequest, agent: Agent = Depends(get_agent)):
    """Stream a message using Agno's built-in streaming with tool calls"""
    if not chat_request.session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required for conversation continuity",
        )

    async def generate_stream():
        """Generate Server-Sent Events stream using Agno's built-in streaming"""
        # Use Agno's built-in streaming with tool calls
        response_stream = await agent.arun(
            chat_request.message,
            user_id=chat_request.user_id,
            session_id=chat_request.session_id,
            stream=True,
            stream_intermediate_steps=True,
        )

        async for event in response_stream:
            # Format event as proper JSON for frontend consumption
            yield _format_sse_data(event)

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@chat_router.get("/memory/{user_id}")
async def get_user_memories(user_id: str, agent: Agent = Depends(get_agent)):
    """Get user memories from the agent's memory system"""
    if not hasattr(agent, "memory") or agent.memory is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Memory system not available",
        )

    # Use Agno's built-in memory API directly
    memories = agent.memory.get_user_memories(user_id=user_id)  # type: ignore

    # Return Agno memory data directly
    return {"memories": memories, "count": len(memories), "user_id": user_id}


@chat_router.delete("/memory/{user_id}")
async def clear_user_memories(user_id: str, agent: Agent = Depends(get_agent)):
    """Clear all memories for a specific user using standard Agno method"""
    if not hasattr(agent, "memory") or agent.memory is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Memory system not available",
        )

    # Use Agno's built-in clear method directly
    agent.memory.clear()

    return {"message": f"Memories cleared for user {user_id}"}


@chat_router.get("/sessions/{user_id}")
async def get_user_sessions(user_id: str, agent: Agent = Depends(get_agent)):
    """Get all session IDs for a specific user using standard Agno method"""
    if not hasattr(agent, "storage") or agent.storage is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Storage system not available",
        )

    # Use Agno's built-in storage API directly
    sessions = agent.storage.get_all_session_ids(user_id)

    return {"sessions": sessions, "count": len(sessions), "user_id": user_id}


@chat_router.get("/history/{session_id}")
async def get_session_history(session_id: str, agent: Agent = Depends(get_agent)):
    """Get conversation history for a specific session using standard Agno method"""
    # Use Agno's built-in method directly
    messages = agent.get_messages_for_session(session_id=session_id)

    # Return Agno message data directly
    return {
        "history": messages,
        "session_id": session_id,
        "count": len(messages),
    }
