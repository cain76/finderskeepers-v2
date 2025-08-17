# FindersKeepers v2 Project Overview

## Purpose
FindersKeepers v2 is a personal AI agent knowledge hub built with containerized microservices architecture. It tracks agent sessions, manages documentation, and provides intelligent knowledge retrieval across multiple AI interactions. The system serves as an "AI GOD MODE" with persistent memory capabilities.

## Tech Stack

### Core Services
- **Backend**: FastAPI (Python 3.12+) with uvicorn
- **Databases**: 
  - PostgreSQL + pgvector (vector embeddings, relational data)
  - Neo4j (knowledge graph for entity relationships)
  - Qdrant (high-performance vector search)
  - Redis (caching and session management)
- **Frontend**: React 18 with TypeScript, Vite, Material-UI, TailwindCSS
- **AI/ML**: Ollama (Llama3 8B), mxbai-embed-large embeddings
- **Infrastructure**: Docker & Docker Compose v2, NVIDIA CUDA (RTX 2080 Ti)
- **Automation**: n8n (deprecated/optional), MCP server integration

### Key Technologies
- **Document Processing**: unstructured, langchain-community, EasyOCR, Whisper
- **Monitoring**: structlog, prometheus-client, psutil
- **Authentication**: python-jose, passlib with bcrypt
- **HTTP**: httpx for async requests, aiofiles for file operations

## Architecture
Microservices architecture with Docker containers:
- services/diary-api/ - FastAPI backend
- services/mcp-session-server/ - MCP server for Claude Desktop
- services/crawl4ai-service/ - Web scraper service  
- fk2_frontend/ - React TypeScript frontend
- scripts/ - Management and deployment utilities