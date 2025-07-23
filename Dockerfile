FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install Poetry and system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install poetry

# Configure Poetry and NLTK
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    NLTK_DATA=/usr/local/share/nltk_data

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy Poetry files first for better caching
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --only=main --no-root

# Install NLTK for unstructured library
RUN poetry run pip install nltk

# Install NLTK data for unstructured library (as root before switching user)
RUN mkdir -p /usr/local/share/nltk_data && poetry run python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); nltk.download('averaged_perceptron_tagger_eng'); nltk.download('maxent_ne_chunker'); nltk.download('words'); nltk.download('stopwords'); nltk.download('omw-1.4')" && chmod -R 755 /usr/local/share/nltk_data

# Create home directory for appuser and set permissions
RUN mkdir -p /home/appuser && chown -R appuser:appuser /home/appuser

# Copy application code
COPY src/ ./src/
COPY data/ ./data/

# Change ownership to app user
RUN chown -R appuser:appuser /app

# Switch to app user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD poetry run python -c "import sys; sys.exit(0)"

# Default command
CMD ["poetry", "run", "python", "-m", "src.api.main"]

# Production stage
FROM base AS production

# Set production environment
ENV FPT_AGENT_ENVIRONMENT=production

# Expose port
EXPOSE 8000

# Run application
CMD ["poetry", "run", "python", "-m", "src.api.main"]