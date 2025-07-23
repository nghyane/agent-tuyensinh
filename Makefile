# FPT University Agent - Refactored Makefile

.PHONY: help install demo-performance api test-cov clean docker-build docker-run docker-dev docker-stop structure

# Installation
install:
	@echo "📦 Installing production dependencies..."
	chmod +x activate_env.sh 
	./activate_env.sh
	pip install -r requirements.txt

api: ## Run FPT Agent API server
	@echo "🚀 Starting FPT University Agent API Server..."
	@python src/api/main.py


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

docker-stop:
	@echo "🐳 Stopping Docker services..."
	docker-compose down


# Show project structure
structure:
	@echo "📁 Project structure:"
	@tree -I '__pycache__|*.pyc|.git|.env' -L 3 .
