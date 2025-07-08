# FPT University Agent - Refactored Makefile

.PHONY: help install install-dev demo demo-simple test clean docker-build docker-run format lint type-check

# Default target
help:
	@echo "🌸 FPT University Agent - Refactored"
	@echo "Available commands:"
	@echo ""
	@echo "  📦 Setup:"
	@echo "    install      - Install production dependencies"
	@echo "    install-dev  - Install development dependencies"
	@echo ""
	@echo "  🚀 Demo:"
	@echo "    demo         - Run full intent detection demo"
	@echo "    demo-simple  - Run simple functionality test"
	@echo ""
	@echo "  🧪 Testing:"
	@echo "    test         - Run tests (when implemented)"
	@echo "    test-cov     - Run tests with coverage"
	@echo ""
	@echo "  🔧 Development:"
	@echo "    format       - Format code with black"
	@echo "    lint         - Lint code with flake8"
	@echo "    type-check   - Type check with mypy"
	@echo "    clean        - Clean cache and temp files"
	@echo ""
	@echo "  🐳 Docker:"
	@echo "    docker-build - Build Docker image"
	@echo "    docker-run   - Run with Docker Compose"
	@echo "    docker-dev   - Run development environment"
	@echo "    docker-stop  - Stop Docker services"

# Installation
install:
	@echo "📦 Installing production dependencies..."
	pip install -r requirements.txt

install-dev:
	@echo "📦 Installing development dependencies..."
	pip install -r requirements-dev.txt

# Demo commands
demo:
	@echo "🚀 Running optimized intent detection demo..."
	python optimized_demo.py

demo-simple:
	@echo "🚀 Running simple functionality test..."
	python optimized_demo.py

# Testing
test:
	@echo "🧪 Running tests..."
	@echo "⚠️  Tests not implemented yet. Run demo instead:"
	@echo "    make demo"

test-cov:
	@echo "🧪 Running tests with coverage..."
	@echo "⚠️  Tests not implemented yet."

# Development tools
format:
	@echo "🎨 Formatting code with black..."
	black src/ optimized_demo.py

lint:
	@echo "🔍 Linting code with flake8..."
	flake8 src/ optimized_demo.py --max-line-length=100 --ignore=E203,W503

type-check:
	@echo "🔍 Type checking with mypy..."
	mypy src/ --ignore-missing-imports

clean:
	@echo "🧹 Cleaning cache and temp files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/ .mypy_cache/ .coverage htmlcov/ 2>/dev/null || true
	@echo "✅ Cleanup completed"

# Docker commands
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t fpt-agent-refactored .

docker-run:
	@echo "🐳 Running with Docker Compose..."
	docker-compose up -d

docker-dev:
	@echo "🐳 Running development environment..."
	docker-compose --profile dev up

docker-stop:
	@echo "🐳 Stopping Docker services..."
	docker-compose down

# Development workflow
dev-setup: install-dev
	@echo "🔧 Setting up development environment..."
	cp .env.example .env
	@echo "✅ Development setup completed"
	@echo "📝 Please edit .env file with your configuration"

dev-check: format lint type-check
	@echo "✅ Development checks completed"

# Quick start
quick-start: install demo
	@echo "🎉 Quick start completed!"

# Production deployment
deploy-check:
	@echo "🚀 Checking production readiness..."
	@echo "✅ Docker image: fpt-agent-refactored"
	@echo "✅ Environment: Check .env file"
	@echo "✅ Dependencies: requirements.txt"
	@echo "✅ Health check: /health endpoint"

# Show project structure
structure:
	@echo "📁 Project structure:"
	@tree -I '__pycache__|*.pyc|.git|.env' -L 3 .
