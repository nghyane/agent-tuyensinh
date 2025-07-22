# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Development Setup
```bash
make install          # Install production dependencies from requirements.txt
cp env.example .env   # Copy environment configuration template
```

### Running the Application
```bash
# Direct execution (fastest way to get started)
python demo.py        # Run FPT Agent demo with predefined questions
python src/api/main.py  # Start FastAPI server

# Available Make targets
make api             # Run FPT Agent API server
make demo-performance # Run agno_demo.py with performance monitoring and DEBUG logging
make clean           # Clean __pycache__, .pyc, .pyo files and build artifacts
```

### Docker Operations
```bash
make docker-build     # Build Docker image (fpt-agent-refactored)
make docker-run       # Run production stack with Redis + Qdrant services
make docker-stop      # Stop all Docker services
```

### Project Structure
```bash
make structure        # Display project tree structure (requires tree command)
```

## Architecture Overview

This is a Vietnamese language intent detection system built with Clean Architecture principles:

### Project Structure
```
src/
├── core/                           # 🧠 Core Business Logic
│   ├── domain/                     # Domain entities, value objects
│   │   └── entities.py            # IntentResult, IntentRule, DetectionContext
│   └── application/                # Application services and use cases
│       └── services/
│           └── hybrid_intent_service.py     # Main orchestrator
├── agno_integration/               # 🤖 Agno Framework Integration
│   ├── __init__.py                # Agno package exports
│   └── intent_tool.py             # IntentDetectionTool for Agno agents
├── api/                           # 🌐 REST API Layer
│   ├── main.py                    # FastAPI application entry point
│   ├── settings.py                # API configuration settings
│   ├── agents/
│   │   └── fpt_agent.py          # FPT University agent implementation
│   ├── factories/
│   │   ├── app_factory.py        # FastAPI application factory
│   │   └── service_factory.py    # Dependency injection factory
│   └── routes/
│       ├── base.py               # Base router
│       ├── health.py             # Health check endpoints
│       ├── chat.py               # Chat/agent endpoints
│       ├── playground.py         # Agno playground interface
│       └── v1_router.py          # API v1 router
├── infrastructure/                 # 🏗️ Infrastructure Layer
│   ├── intent_detection/
│   │   ├── rule_based.py          # Rule-based detection impl
│   │   └── rule_loader.py         # Rule loading utilities
│   ├── vector_stores/
│   │   └── qdrant_store.py        # Vector search implementation
│   ├── embeddings/
│   │   └── openai_embeddings.py   # OpenAI embedding provider
│   └── caching/
│       └── memory_cache.py        # In-memory caching
└── shared/                         # 🤝 Shared utilities
    ├── types.py                    # Type definitions
    └── utils/
        ├── text_processing.py      # Vietnamese text processing
        └── template_manager.py     # Template management utilities
```

### Detection Flow
1.  **Rule-based detection** (`rule_based.py`) - Fast keyword/pattern matching with early exit at confidence ≥ 0.8
2.  **Vector search** (`qdrant_store.py` + embeddings) - Only triggered if rule confidence < 0.8
3.  **Hybrid selection** - Chooses best result based on confidence thresholds
4.  **Multi-level caching** - Memory cache + optional Redis for performance

### Key Services and Components
- `HybridIntentDetectionService` (`src/core/application/services/`): Main orchestrator combining rule-based + vector search
- `RuleBasedDetectorImpl` (`src/infrastructure/intent_detection/`): Fast keyword/pattern matching for Vietnamese text
- `QdrantVectorStore` (`src/infrastructure/vector_stores/`): Vector similarity search (optional, requires Qdrant)
- `VietnameseTextProcessor` (`src/shared/utils/text_processing.py`): Text normalization and preprocessing for Vietnamese
- `TemplateManager` (`src/shared/utils/template_manager.py`): Manages response templates and formatting
- `IntentDetectionTool` (`src/agno_integration/intent_tool.py`): Agno framework wrapper exposing intent detection as agent tool

### Configuration and Environment Variables
Environment variables are defined in `env.example` (copy to `.env`):

**Core Settings:**
- `OPENAI_API_KEY`: Required for OpenAI embeddings and LLM calls.
- `OPENAI_BASE_URL`: OpenAI API endpoint (default: `https://api.openai.com/v1`).

**API Server:**
- `FPT_AGENT_HOST`: Server host (default: `0.0.0.0`).
- `FPT_AGENT_PORT`: Server port (default: `8000`).
- `FPT_AGENT_RELOAD`: Auto-reload for development (default: `false`).
- `FPT_AGENT_DOCS_ENABLED`: Enable/disable API docs (default: `true`).

**Intent Detection:**
- `FPT_AGENT_INTENT_DETECTION_TIMEOUT`: Timeout for intent detection in seconds (default: `10.0`).
- `FPT_AGENT_MAX_QUERY_LENGTH`: Maximum query length (default: `1000`).

**Agent Configuration:**
- `FPT_AGENT_DEFAULT_MODEL`: LLM model to use (default: `gpt-4o`).

**CORS Configuration:**
- `FPT_AGENT_CORS_ORIGIN_LIST`: Comma-separated list of allowed CORS origins.

**Logging:**
- `FPT_AGENT_LOG_LEVEL`: Logging level (e.g., `INFO`, `DEBUG`) (default: `INFO`).

**Optional Services:**
- `QDRANT_HOST` / `QDRANT_PORT`: For vector search (commented out in `env.example`).
- `REDIS_URL`: For caching (commented out in `env.example`).

### Data Files
- `data/production_rules.json`: Intent detection rules (keywords, patterns, weights)
- `data/intent-examples.json`: Training examples for vector search
- `data/templates.json`: Response templates for different intents

### Dependencies and Tech Stack
**Core Framework:**
- **Agno Framework (>=1.7.5)**: Multi-agent orchestration and reasoning capabilities
- **FastAPI + Uvicorn**: REST API server with OpenAPI documentation
- **Pydantic (>=2.0.0)**: Data validation and serialization
- **asyncio-mqtt**: Async framework support

**Text Processing:**
- **unidecode**: Vietnamese text normalization
- **structlog**: Structured logging with performance tracking

**Optional Integrations:**
- **qdrant-client**: Vector similarity search
- **openai**: Embeddings and LLM provider

### Performance Characteristics
- Rule-based detection: ~1-2ms average response time
- Vector search: ~50-100ms when enabled
- Early exit optimization: Reduces processing time by 75%
- Multi-level caching: 85% hit rate in typical usage

### Agno Framework Integration

The system now supports multi-agent orchestration through the Agno framework:

#### IntentDetectionTool Features:
- **Agent Tool Integration**: Exposes intent detection as a callable tool for Agno agents
- **Rich Formatting**: Provides emoji-rich, structured responses with action suggestions
- **Auto Language Detection**: Automatically detects Vietnamese vs English queries
- **Action Suggestions**: Context-aware recommendations based on detected intent
- **Metadata Reporting**: Detailed performance and confidence metrics

#### Usage Patterns:
```python
# Create tool from existing service
intent_tool = create_intent_detection_tool(intent_service)

# Add to Agno agent
agent = Agent(
    model=OpenAILike(...),
    tools=[ReasoningTools(), intent_tool],
    instructions="Always use detect_intent before responding..."
)

# Run with async support
response = await agent.arun("Học phí FPT bao nhiêu?")
```

#### API Integration:
- **REST API**: FastAPI-based server at `/v1/agent/chat`
- **Streaming Support**: Real-time response streaming via `/v1/agent/chat/stream`
- **Playground Interface**: Agno playground at `/playground` for interactive testing
- **Health Monitoring**: Health checks at `/health` and `/v1/health`
- **Interactive Docs**: Swagger UI at `/docs`, ReDoc at `/redoc`

### Development Guidelines

**Clean Architecture Compliance:**
- Respect layer boundaries: domain → application → infrastructure
- Don't bypass layers or create circular dependencies
- Use dependency injection through factories (`src/api/factories/`)

**Key Implementation Notes:**
- All detection flows use async/await patterns
- Vietnamese text processing is critical - always use `VietnameseTextProcessor`
- Structured logging with performance metrics is built-in via structlog
- Entry points: `src/api/main.py` for API server, `demo.py` for testing

**Environment Setup:**
1. Copy `env.example` to `.env`
2. Set `OPENAI_API_KEY` for full functionality
3. Optional: Configure Qdrant/Redis for enhanced performance

**Adding New Intent Rules:**
Intent rules are defined in `data/production_rules.json`. The rule structure includes:
- `intent_id`: Unique identifier
- `keywords`: List of keywords for matching
- `patterns`: Regex patterns for complex matching
- `weight`: Confidence multiplier
- `description`: Human-readable description

**API Endpoints:**
- Health checks: `/health`, `/v1/health`
- Agent chat: `/v1/agent/chat` (POST)
- Streaming chat: `/v1/agent/chat/stream` (POST)
- Playground interface: `/playground` (Agno interactive playground)
- Interactive docs: `/docs` (Swagger UI), `/redoc` (ReDoc)
