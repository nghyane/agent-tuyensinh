# AGENTS.md - FPT University Agent Development Guide

## Build/Test Commands
- `make install` - Install production dependencies from requirements.txt
- `make api` - Run FastAPI server (src/api/main.py)
- `python demo.py` - Run agent demo with predefined questions
- `make demo-performance` - Run demo with performance monitoring and DEBUG logging
- `make clean` - Clean __pycache__, .pyc files and build artifacts
- `make docker-build && make docker-run` - Build and run with Docker Compose
- `python test_university_api_tool.py` - Run single test file for UniversityApiTool
- No pytest configured - use individual test files like test_*.py for testing

## Code Style Guidelines
- **Imports**: Absolute imports from src/ (e.g., `from api.factories import ServiceFactory`)
- **Types**: Use Pydantic models, dataclasses, and type hints extensively (see shared/types.py)
- **Async**: Prefer async/await patterns throughout (all services are async)
- **Naming**: snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants
- **Error Handling**: Use custom exception classes (IntentDetectionError, VectorSearchError) and Result[T] pattern
- **Docstrings**: Use triple quotes with brief description, Args/Returns sections
- **Config**: Environment variables with FPT_AGENT_ prefix, use pydantic_settings
- **Architecture**: Follow Clean Architecture - core/domain, core/application, infrastructure, api layers
- **Vietnamese**: Use VietnameseTextProcessor for text normalization and processing
- **Logging**: Use structlog for structured logging with performance tracking
- **Services**: Initialize via ServiceFactory with dependency injection pattern
- **Enums**: Use typed enums for constants (DetectionMethod, ConfidenceLevel, IntentCategory)
- **Context Managers**: Implement async context managers for resource management (e.g., UniversityApiTool)