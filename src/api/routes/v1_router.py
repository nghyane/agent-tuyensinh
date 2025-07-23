"""
V1 API router
"""

from fastapi import APIRouter

from api.routes.health import health_router
from api.routes.base import base_router
from api.routes.chat import chat_router
from api.routes.knowledge_routes import router as knowledge_router

v1_router = APIRouter(prefix="/v1")

# Include all route modules
v1_router.include_router(health_router)
v1_router.include_router(base_router)
v1_router.include_router(chat_router)
v1_router.include_router(knowledge_router) 

