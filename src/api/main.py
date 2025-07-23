"""
FastAPI main application for FPT University Agent
"""

import sys
from pathlib import Path

import uvicorn

# Add src to Python path
current_dir = Path(__file__).parent.parent.parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Import after path setup
from api.factories import AppFactory  # noqa: E402
from api.settings import api_settings  # noqa: E402

# Create app factory and application
app_factory = AppFactory()
app = app_factory.create_app()


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=api_settings.host,
        port=api_settings.port,
        reload=api_settings.reload,
    )
