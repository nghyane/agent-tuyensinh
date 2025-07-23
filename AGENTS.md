# AGENTS.md - FPT University Agent Development Guide

## Build/Test Commands
- `make dev` - Install all dependencies including dev tools (poetry install --with dev)
- `make install` - Install production dependencies only (poetry install)
- `make api` - Run FastAPI server (src/api/main.py)
- `make test` - Run tests with pytest (poetry run pytest)
- `make lint` - Run linters with auto-fix (black, isort, ruff, mypy)
- `make lint-check` - Run linters without auto-fix (for CI)
- `python demo.py` - Run agent demo with predefined questions
- `make clean` - Clean __pycache__, .pyc files and build artifacts
- `make docker-build && make docker-run` - Build and run with Docker Compose
- **Single test**: `poetry run pytest path/to/test_file.py::test_function` - Run specific test
- **No project tests exist** - Create test files following pytest conventions (test_*.py)

## Code Style Guidelines
- **Package Manager**: Use Poetry for dependency management (pyproject.toml)
- **Imports**: Absolute imports from src/ (e.g., `from api.factories import ServiceFactory`)
- **Formatting**: Black (line-length=88), isort (profile="black"), ruff for linting
- **Types**: Use Pydantic models, dataclasses, and extensive type hints (see shared/common_types.py)
- **Type Checking**: MyPy configured with strict settings, ignore missing imports for external libs
- **Async**: Prefer async/await patterns throughout (all services are async)
- **Naming**: snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants
- **Error Handling**: Use custom exception classes and Result[T] pattern for operations that can fail
- **Docstrings**: Use triple quotes with brief description, Args/Returns sections
- **Config**: Environment variables with FPT_AGENT_ prefix, use pydantic-settings BaseSettings
- **Architecture**: Follow Clean Architecture - core/domain, core/application, infrastructure, api layers
- **Vietnamese**: Use VietnameseTextProcessor for text normalization and processing
- **Logging**: Use structlog for structured logging with performance tracking
- **Services**: Initialize via ServiceFactory with dependency injection pattern
- **Enums**: Use typed enums for constants (DetectionMethod, ConfidenceLevel, IntentCategory)
- **Context Managers**: Implement async context managers for resource management