"""
Chat API endpoints for FPT University Agent
Optimized for Agno framework best practices
"""

import asyncio
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
import logging

# Import Agent type for proper type hints
from agno.agent import Agent

# Configure logging
logger = logging.getLogger(__name__)

chat_router = APIRouter(prefix="/chat", tags=["Chat"])


# Core Pydantic models
class ChatRequest(BaseModel):
    """Chat request with validation"""
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
    """Chat response with Agno metrics and tool calls"""
    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Response timestamp")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Agent run metrics")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Tool calls made during response")


# Dependency injection
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
    """Process chat message with proper error handling"""
    try:
        logger.info(f"Processing message for user {user_id}, session {session_id}")
        
        # Run agent with timeout protection
        response = await asyncio.wait_for(
            agent.arun(message, user_id=user_id, session_id=session_id),
            timeout=60.0
        )
        
        # Handle response according to Agno docs
        if hasattr(response, 'content'):
            response_content = response.content
            metrics = getattr(response, 'metrics', None)
            tool_calls = getattr(response, 'tool_calls', None)
        elif hasattr(response, '__aiter__'):
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
    except Exception as e:
        logger.error(f"Error processing message for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )


def _format_sse_data(data: dict) -> str:
    """Format data as Server-Sent Events"""
    return f"data: {json.dumps(data, default=str)}\n\n"


# API Endpoints
@chat_router.post("/send", response_model=ChatResponse)
async def send_message(chat_request: ChatRequest, agent: Agent = Depends(get_agent)):
    """Send a message to the FPT University Agent"""
    if not chat_request.session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required for conversation continuity"
        )
    
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


@chat_router.post("/stream")
async def stream_message(chat_request: ChatRequest, agent: Agent = Depends(get_agent)):
    """Stream a message using Agno's built-in streaming with tool calls"""
    if not chat_request.session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required for conversation continuity"
        )
    
    async def generate_stream():
        """Generate Server-Sent Events stream using Agno's built-in streaming"""
        try:
            # Use Agno's built-in streaming with tool calls
            response_stream = await agent.arun(
                chat_request.message, 
                user_id=chat_request.user_id, 
                session_id=chat_request.session_id,
                stream=True,
                stream_intermediate_steps=True
            )
            
            async for event in response_stream:
                # Handle different event types from Agno
                if hasattr(event, 'event'):
                    if event.event == "RunResponseContent":
                        yield _format_sse_data({
                            "type": "content",
                            "content": event.content,
                            "session_id": chat_request.session_id,
                            "user_id": chat_request.user_id,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                    elif event.event == "ToolCallStarted":
                        yield _format_sse_data({
                            "type": "tool_call_start",
                            "tool_name": event.tool.name if hasattr(event.tool, 'name') else 'unknown',
                            "tool_args": event.tool.args if hasattr(event.tool, 'args') else {},
                            "session_id": chat_request.session_id,
                            "user_id": chat_request.user_id,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                    elif event.event == "ToolCallCompleted":
                        yield _format_sse_data({
                            "type": "tool_call_complete",
                            "tool_name": event.tool.name if hasattr(event.tool, 'name') else 'unknown',
                            "tool_result": str(event.tool.result) if hasattr(event.tool, 'result') else '',
                            "session_id": chat_request.session_id,
                            "user_id": chat_request.user_id,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                    elif event.event == "RunResponseCompleted":
                        yield _format_sse_data({
                            "type": "final",
                            "session_id": chat_request.session_id,
                            "user_id": chat_request.user_id,
                            "metrics": getattr(event, 'metrics', None),
                            "tool_calls": getattr(event, 'tool_calls', None),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                else:
                    # Fallback for direct content
                    if hasattr(event, 'content') and event.content:
                        yield _format_sse_data({
                            "type": "content",
                            "content": event.content,
                            "session_id": chat_request.session_id,
                            "user_id": chat_request.user_id,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        
        except Exception as e:
            logger.error(f"Error in streaming: {str(e)}")
            yield _format_sse_data({
                "type": "error",
                "error": str(e),
                "session_id": chat_request.session_id,
                "user_id": chat_request.user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    ) 