"""
FastAPI main application for FPT University Agent
"""

import sys
from pathlib import Path

# Add src to Python path
current_dir = Path(__file__).parent.parent.parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from api.factories import AppFactory
from api.settings import api_settings

# Create app factory and application
app_factory = AppFactory()
app = app_factory.create_app()
        

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=api_settings.host,
        port=api_settings.port,
        reload=api_settings.reload
    ) 