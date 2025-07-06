# FindersKeepers v2 FastAPI Backend

AI Agent Knowledge Hub with modern Python packaging using UV.

## Features

- FastAPI web framework with async support
- PostgreSQL + pgvector for vector embeddings
- Neo4j for knowledge graph relationships  
- Qdrant for high-performance vector search
- Redis for caching and session management
- Ollama integration for local LLM inference
- Multi-API support (OpenAI, Anthropic, Google)

## Development

Built with UV for 10-100x faster dependency management:

```bash
# Install dependencies
uv sync

# Run development server
uv run fastapi dev

# Run tests
uv run pytest
```

## Deployment

Optimized Docker container with multi-stage builds, bytecode compilation, and security hardening.