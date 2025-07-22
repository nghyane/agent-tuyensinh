"""
App factory for FPT University Agent
"""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.settings import api_settings
from api.routes.v1_router import v1_router
from api.routes.base import base_router
from api.routes.playground import create_playground_router
from .service_factory import ServiceFactory


class AppFactory:
    """Factory for creating FastAPI application"""

    def __init__(self):
        self.service_factory = ServiceFactory()
        self.playground_router = None

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Lifespan context manager for FastAPI app"""
        # Startup - initialize services
        print("🚀 Starting FPT University Agent API...")
        await self.service_factory.initialize_services(
            model_id=api_settings.default_model,
            debug_mode=False
        )

        # Get agent instance once
        agent = self.service_factory.get_agent()

        # Set global agent instance
        import api.routes
        api.routes.fpt_agent = agent

        # Create playground router after agent is initialized
        if agent is not None:
            print("🔧 Creating playground router...")
            self.playground_router = create_playground_router(agent)
            app.include_router(self.playground_router, prefix="/v1")
            print("✅ Playground router added successfully")
        else:
            print("⚠️  Agent not initialized, skipping playground router")

        yield
        # Shutdown (if needed)
        print("🛑 Shutting down FPT University Agent API...")

    def create_app(self) -> FastAPI:
        """Create and configure FastAPI application"""

        # Create FastAPI App
        app: FastAPI = FastAPI(
            title=api_settings.title,
            version=api_settings.version,
            description=api_settings.description,
            docs_url="/docs" if api_settings.docs_enabled else None,
            redoc_url="/redoc" if api_settings.docs_enabled else None,
            openapi_url="/openapi.json" if api_settings.docs_enabled else None,
            lifespan=self.lifespan,
        )

        # Add CORS middleware first
        app.add_middleware(
            CORSMiddleware,
            allow_origins=api_settings.cors_origin_list or ["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["*"]
        )

        # Add v1 router after CORS middleware
        app.include_router(v1_router)

        # Add base routes
        app.include_router(base_router)

        return app

    def get_service_factory(self) -> ServiceFactory:
        """Get the service factory"""
        return self.service_factory
