"""
Chat API endpoints for FPT University Agent
Optimized for Agno framework best practices
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
import logging

# Import Agent type for proper type hints
from agno.agent import Agent
from agno.memory.v2.memory import Memory

# Configure logging
logger = logging.getLogger(__name__)

chat_router = APIRouter(prefix="/chat", tags=["Chat"])


# Enhanced Pydantic models with validation
class ChatRequest(BaseModel):
    """Enhanced chat request with validation"""
    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    user_id: str = Field(..., min_length=1, max_length=100, description="Unique user identifier")
    session_id: Optional[str] = Field(None, max_length=100, description="Session identifier for conversation continuity")
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()


class ChatResponse(BaseModel):
    """Enhanced chat response with Agno metrics and tool calls"""
    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Response timestamp")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Agent run metrics")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Tool calls made during response")


class MemoryResponse(BaseModel):
    """Memory response model"""
    memories: List[Dict[str, Any]] = Field(..., description="User memories")
    count: int = Field(..., description="Number of memories")
    user_id: str = Field(..., description="User identifier")


class SessionResponse(BaseModel):
    """Session response model"""
    sessions: List[str] = Field(..., description="Session identifiers")
    count: int = Field(..., description="Number of sessions")
    user_id: str = Field(..., description="User identifier")


class HistoryResponse(BaseModel):
    """History response model"""
    history: List[Dict[str, str]] = Field(..., description="Conversation history")
    session_id: str = Field(..., description="Session identifier")
    count: int = Field(..., description="Number of messages")


# Dependency injection with error handling
async def get_agent() -> Agent:
    """Get agent instance with proper error handling"""
    from api.routes import fpt_agent
    
    if fpt_agent is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    return fpt_agent


# Core chat functionality
async def _process_chat_message(agent: Agent, message: str, user_id: str, session_id: Optional[str] = None) -> tuple[str, Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]]]:
    """Process chat message with proper error handling and logging"""
    try:
        logger.info(f"Processing message for user {user_id}, session {session_id}")
        
        # Run agent with timeout protection
        response = await asyncio.wait_for(
            agent.arun(message, user_id=user_id, session_id=session_id),
            timeout=60.0
        )
        
        # Handle response according to Agno docs
        if hasattr(response, 'content'):
            # Direct response object
            response_content = response.content
            metrics = getattr(response, 'metrics', None)
            tool_calls = getattr(response, 'tool_calls', None)
        elif hasattr(response, '__aiter__'):
            # Streaming response
            response_content = ""
            metrics = None
            tool_calls = None
            async for chunk in response:
                if hasattr(chunk, 'content'):
                    response_content += chunk.content
                if metrics is None and hasattr(chunk, 'metrics'):
                    metrics = chunk.metrics
                if tool_calls is None and hasattr(chunk, 'tool_calls'):
                    tool_calls = chunk.tool_calls
        else:
            # Fallback
            response_content = str(response)
            metrics = None
            tool_calls = None
            
        logger.info(f"Successfully processed message for user {user_id}")
        return response_content, metrics, tool_calls
        
    except asyncio.TimeoutError:
        logger.error(f"Timeout processing message for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timeout - agent took too long to respond"
        )
    except ImportError as e:
        logger.error(f"Import error for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service dependencies not available"
        )
    except ValueError as e:
        logger.error(f"Invalid parameters for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error processing message for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )


# API Endpoints
@chat_router.post("/send", response_model=ChatResponse)
async def send_message(chat_request: ChatRequest, agent: Agent = Depends(get_agent)):
    """Send a message to the FPT University Agent"""
    # Validate session ID first for better performance
    if not chat_request.session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required for conversation continuity. Please provide a session_id in your request."
        )
    
    # Process chat message
    response_content, metrics, tool_calls = await _process_chat_message(
        agent=agent,
        message=chat_request.message,
        user_id=chat_request.user_id,
        session_id=chat_request.session_id
    )
    
    return ChatResponse(
        response=response_content,
        session_id=chat_request.session_id,
        user_id=chat_request.user_id,
        metrics=metrics,
        tool_calls=tool_calls
    )


@chat_router.get("/memory/{user_id}", response_model=MemoryResponse)
async def get_user_memories(user_id: str, agent: Agent = Depends(get_agent)):
    """Get user memories from the agent's memory system"""
    if not hasattr(agent, 'memory') or agent.memory is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Memory system not available"
        )
    
    # Use memory API directly with type assertion
    memories = agent.memory.get_user_memories(user_id=user_id)  # type: ignore
    
    # Convert memories to serializable format
    memory_list = []
    for memory in memories:
        try:
            memory_dict = {
                "content": str(memory),
                "importance": getattr(memory, 'importance', None),
                "created_at": getattr(memory, 'created_at', None),
                "topics": getattr(memory, 'topics', [])
            }
            memory_list.append(memory_dict)
        except Exception as e:
            logger.warning(f"Error serializing memory: {str(e)}")
            continue
    
    return MemoryResponse(
        memories=memory_list,
        count=len(memory_list),
        user_id=user_id
    )


@chat_router.delete("/memory/{user_id}")
async def clear_user_memories(user_id: str, agent: Agent = Depends(get_agent)):
    """Clear all memories for a specific user using standard Agno method"""
    if not hasattr(agent, 'memory') or agent.memory is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Memory system not available"
        )
    
    # Use standard Agno method to clear all memories
    agent.memory.clear()
    
    return {"message": f"Memories cleared for user {user_id}"}


@chat_router.get("/sessions/{user_id}", response_model=SessionResponse)
async def get_user_sessions(user_id: str, agent: Agent = Depends(get_agent)):
    """Get all session IDs for a specific user using standard Agno method"""
    if not hasattr(agent, 'storage') or agent.storage is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Storage system not available"
        )
    
    sessions = agent.storage.get_all_session_ids(user_id)
    
    return SessionResponse(
        sessions=sessions,
        count=len(sessions),
        user_id=user_id
    )


@chat_router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_session_history(session_id: str, agent: Agent = Depends(get_agent)):
    """Get conversation history for a specific session using standard Agno method"""
    # Use the standard Agno method with session_id parameter
    messages = agent.get_messages_for_session(session_id=session_id)
    
    # Convert to response format
    history = [
        {"role": msg.role, "content": msg.content or ""} 
        for msg in messages if msg.content is not None
    ]
    
    return HistoryResponse(
        history=history,
        session_id=session_id,
        count=len(history)
    ) 