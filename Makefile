# FPT University Agent - Refactored Makefile

.PHONY: help install dev api test lint clean docker-build docker-run docker-stop

# Installation
install: ## Install production dependencies
	@echo "📦 Installing dependencies..."
	@which poetry > /dev/null || (echo "❌ Poetry not found. Installing Poetry..." && curl -sSL https://install.python-poetry.org | python3 -)
	@export PATH="$$HOME/.local/bin:$$PATH" && poetry install
	@echo "✅ Dependencies installed"

dev: ## Install all dependencies (including dev)
	@echo "📦 Installing all dependencies..."
	@which poetry > /dev/null || (echo "❌ Poetry not found. Installing Poetry..." && curl -sSL https://install.python-poetry.org | python3 -)
	@export PATH="$$HOME/.local/bin:$$PATH" && poetry install --with dev
	@echo "✅ All dependencies installed"

# Development
test: ## Run tests
	@echo "🧪 Running tests..."
	@export PATH="$$HOME/.local/bin:$$PATH" && poetry run pytest

lint: ## Run linters and type checker with auto-fix
	@echo "🔍 Running linters with auto-fix..."
	@export PATH="$$HOME/.local/bin:$$PATH" && poetry run black src/
	@export PATH="$$HOME/.local/bin:$$PATH" && poetry run isort src/
	@export PATH="$$HOME/.local/bin:$$PATH" && poetry run ruff check --fix src/
	@export PATH="$$HOME/.local/bin:$$PATH" && poetry run mypy --explicit-package-bases src/

lint-check: ## Run linters without auto-fix (for CI)
	@echo "🔍 Running linters (check only)..."
	@export PATH="$$HOME/.local/bin:$$PATH" && poetry run black --check src/
	@export PATH="$$HOME/.local/bin:$$PATH" && poetry run isort --check-only src/
	@export PATH="$$HOME/.local/bin:$$PATH" && poetry run ruff check src/
	@export PATH="$$HOME/.local/bin:$$PATH" && poetry run mypy --explicit-package-bases src/

api: ## Run API server
	@echo "🚀 Starting API server..."
	@export PATH="$$HOME/.local/bin:$$PATH" && poetry run python src/api/main.py


clean: ## Clean cache and temp files
	@echo "🧹 Cleaning cache and temp files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/ .mypy_cache/ .coverage htmlcov/ 2>/dev/null || true
	@echo "✅ Cleanup completed"

# Docker
docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t fpt-agent .

docker-run: ## Run with Docker Compose
	@echo "🐳 Running with Docker Compose..."
	docker-compose up -d

docker-stop: ## Stop Docker services
	@echo "🐳 Stopping Docker services..."
	docker-compose down

# Help
help: ## Show this help
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
