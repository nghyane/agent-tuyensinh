"""
App factory for FPT University Agent
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from api.routes.base import base_router
from api.routes.playground import create_playground_router
from api.routes.v1_router import v1_router
from api.settings import api_settings

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
            model_id=api_settings.default_model, debug_mode=False
        )

        # Pass service_factory to app state so it can be accessed in requests
        app.state.service_factory = self.service_factory

        # Create a temporary agent instance just for creating the playground
        temp_agent_for_playground = self.service_factory.get_fpt_agent()
        if temp_agent_for_playground:
            print("🔧 Creating playground router...")
            self.playground_router = create_playground_router(temp_agent_for_playground)
            app.include_router(self.playground_router, prefix="/v1")
            print("✅ Playground router added successfully")
        else:
            print("⚠️  Agent could not be created, skipping playground router")

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
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )

        # Add v1 router after CORS middleware
        app.include_router(v1_router)

        # Add base routes
        app.include_router(base_router)

        return app

    def get_service_factory(self) -> ServiceFactory:
        """Get the service factory"""
        return self.service_factory
