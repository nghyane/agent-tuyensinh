"""
Base routes for FPT University Agent API
"""

from fastapi import APIRouter

base_router = APIRouter()


@base_router.options("/{full_path:path}", include_in_schema=False)
async def options_handler(full_path: str):
    """Handle OPTIONS requests for CORS preflight"""
    return {"message": "OK"}
