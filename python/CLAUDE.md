# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Development Setup
```bash
make install           # Install production dependencies
make install-dev       # Install development dependencies  
make dev-setup         # Complete development environment setup (includes .env)
make quick-start       # Install and run demo (fastest way to get started)
```

### Running the Application
```bash
make demo             # Run optimized intent detection demo
make demo-simple      # Run simple functionality test
python optimized_demo.py  # Direct demo execution
python production_test.py  # Run production test suite
```

### Code Quality
```bash
make format           # Format code with black
make lint             # Lint with flake8 (max-line-length=100, ignore=E203,W503)
make type-check       # Type check with mypy (ignore-missing-imports)
make dev-check        # Run all checks (format + lint + type-check)
make clean            # Clean cache and temp files
```

### Docker Operations
```bash
make docker-build     # Build Docker image (fpt-agent-refactored)
make docker-run       # Run production stack with Redis/Qdrant
make docker-dev       # Run development environment
make docker-stop      # Stop Docker services
```

### Testing
- Primary testing via `make demo` and `python production_test.py`
- Tests framework: pytest (configured but not fully implemented)
- `make test` will show warning - use demos for verification
- `make dev-check` for code quality verification

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
│           ├── hybrid_intent_service.py     # Main orchestrator
│           └── vector_indexing_service.py   # Vector management
├── infrastructure/                 # 🏗️ Infrastructure Layer
│   ├── intent_detection/
│   │   ├── rule_based.py          # Rule-based detection impl
│   │   └── rule_loader.py         # Rule loading utilities
│   ├── vector_stores/
│   │   └── qdrant_store.py        # Vector search implementation
│   ├── embeddings/
│   │   ├── openai_embeddings.py   # OpenAI embedding provider
│   │   └── local_embeddings.py    # Local embedding models
│   ├── caching/
│   │   └── memory_cache.py        # In-memory caching
│   └── reranking/
│       └── cross_encoder_reranker.py  # Cross-encoder reranking
└── shared/                         # 🤝 Shared utilities
    ├── types.py                    # Type definitions
    └── utils/
        ├── text_processing.py      # Vietnamese text processing
        └── metrics.py              # Performance metrics
```

### Detection Flow
1. **Rule-based detection** (`rule_based.py`) - Fast keyword/pattern matching with early exit at confidence ≥ 0.8
2. **Vector search** (`qdrant_store.py` + embeddings) - Only triggered if rule confidence < 0.8
3. **Cross-encoder reranking** - Optional refinement of vector results
4. **Hybrid selection** - Chooses best result based on confidence thresholds
5. **Multi-level caching** - Memory cache + optional Redis for performance

### Key Services
- `HybridIntentDetectionService`: Main orchestrator combining rule-based + vector search
- `RuleBasedDetectorImpl`: Fast keyword/pattern matching for Vietnamese text
- `QdrantVectorStore`: Vector similarity search (optional, requires Qdrant)
- `VietnameseTextProcessor`: Text normalization and preprocessing for Vietnamese
- `VectorIndexingService`: Manages vector embeddings and indexing

### Configuration
- Uses environment variables (see `.env.example`)
- Key configs: `FPT_AGENT_ENVIRONMENT`, `FPT_AGENT_CACHE_BACKEND`, `FPT_AGENT_VECTOR_BACKEND`
- HybridConfig class in `hybrid_intent_service.py` controls detection thresholds

### Data Files
- `data/production_rules.json`: Intent detection rules (keywords, patterns, weights)
- `data/intent-examples.json`: Training examples for vector search

### Dependencies
- **Core**: asyncio, pydantic, structlog, unidecode, typing-extensions
- **Optional**: qdrant-client, openai, sentence-transformers, torch (for vector search)
- **Dev**: pytest, mypy, black, flake8, pre-commit, pytest-asyncio

### Performance Characteristics
- Rule-based detection: ~1-2ms average
- Vector search: ~50-100ms when enabled
- Early exit optimization reduces 75% of processing time
- Multi-level caching provides 85% hit rate

### Development Notes
- Follow Clean Architecture boundaries - don't bypass layers
- All detection flows are async/await
- Vietnamese text processing is critical - use `VietnameseTextProcessor`
- Type hints are enforced with mypy
- Use structured logging with performance metrics
- Entry points: `optimized_demo.py` for demos, `production_test.py` for testing