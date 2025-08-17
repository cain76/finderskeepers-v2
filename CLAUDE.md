# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 PROJECT ROADMAP

**CRITICAL**: Always check `.claude/ROADMAP.md` for current project status, priorities, and next steps. This living document tracks our progress through all phases of FindersKeepers v2 development and contains critical architectural decisions.

## Project Overview

FindersKeepers v2 is a personal AI agent knowledge hub built with a containerized microservices architecture. It tracks agent sessions, manages documentation, and provides intelligent knowledge retrieval across multiple AI interactions.

## Development Commands

### Starting/Stopping Services

```bash
# Start all services (recommended)
./scripts/start-all.sh

# Stop all services
./scripts/stop-all.sh

# Start specific services
docker compose up -d fastapi
docker compose up -d postgres neo4j redis qdrant

# View logs
docker compose logs -f
docker compose logs -f fastapi  # specific service
```

### Development & Testing

```bash
# FastAPI development (requires Docker services running)
cd services/diary-api
uv sync  # Install dependencies (preferred package manager)
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Alternative with pip
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend development
cd fk2_frontend
npm install
npm run dev  # Starts on port 3000

# Run tests (when implemented)
cd services/diary-api && uv run pytest
cd fk2_frontend && npm test

# Code formatting & linting
cd services/diary-api
uv run black .
uv run isort .

cd fk2_frontend
npm run lint
```

### MCP Session Management

```bash
# Clean up stuck MCP Knowledge Server processes
./scripts/cleanup-mcp-sessions.sh

# Clean up zombie sessions in database (mark old active sessions as ended)
./scripts/cleanup-zombie-sessions.py --dry-run  # Preview what would be cleaned
./scripts/cleanup-zombie-sessions.py --max-age 6 --force  # Clean sessions older than 6 hours

# Start MCP Knowledge Server (with proper signal handling)
cd services/mcp-knowledge-server
source .venv/bin/activate
python src/knowledge_server.py

# Stop MCP server gracefully (use Ctrl+C, not kill -9)
# Server now handles SIGTERM and SIGINT signals properly
```

### Database Operations

```bash
# PostgreSQL direct access
docker exec -it fk2_postgres psql -U finderskeepers -d finderskeepers_v2

# Neo4j browser access
# Navigate to http://localhost:7474 (neo4j/fk2025neo4j)

# Redis CLI
docker exec -it fk2_redis redis-cli
```

## Architecture

### Core Services

- **FastAPI Backend** (`services/diary-api/`) - API endpoints for agent session tracking, knowledge queries, and document management
- **PostgreSQL + pgvector** - Vector embeddings, relational data, and document storage
- **Neo4j** - Knowledge graph for entity relationships and context linking
- **Qdrant** - High-performance vector search for document retrieval
- **Redis** - Caching and session management
- **n8n** - Workflow automation for agent coordination

### Key Data Models

- **AgentSession**: Tracks individual AI agent interactions with context
- **AgentAction**: Logs specific actions within sessions (file edits, commands, etc.)
- **DocumentIngest**: Handles knowledge base document storage and indexing
- **KnowledgeQuery**: Natural language queries against the knowledge graph
- **ConfigChange**: Tracks system configuration changes with rollback capability

### Database Schema

The PostgreSQL schema (`config/pgvector/init.sql`) includes:

- `agent_sessions` - Session tracking with JSONB context
- `agent_actions` - Action logging with file tracking
- `documents` - Document storage with vector embeddings
- `document_chunks` - Chunked content for vector search
- `config_changes` - Configuration change history
- `knowledge_entities` - Neo4j entity references

## API Endpoints

### Agent Session Management

- `POST /api/diary/sessions` - Create new agent session
- `POST /api/diary/actions` - Log agent actions
- `GET /api/diary/search` - Search session history

### Knowledge Management

- `POST /api/knowledge/query` - Natural language knowledge queries
- `POST /api/docs/ingest` - Ingest new documentation
- `GET /api/docs/context` - Get project-specific context

### Configuration Tracking

- `POST /api/config/log-change` - Log configuration changes
- `GET /api/config/history` - Retrieve change history

## Development Workflow

1. **Environment Setup**: Copy `.env.example` to `.env` and configure API keys
2. **Service Dependencies**: Always start database services before FastAPI
3. **Development Mode**: Use `docker compose up -d postgres neo4j redis qdrant` then run FastAPI locally
4. **Testing**: Ensure all services are running before running tests
5. **Database Changes**: Update `config/pgvector/init.sql` for schema changes

## 🚀 Enhanced Session Continuity Workflow

### Starting Your Claude Code Session

**ALWAYS run this first when starting Claude Code:**

```bash
mcp__fk-knowledge__resume_session()
```

This will:
- 🔍 Find your most recent session and load full context
- 📊 Show you exactly what you were working on
- 🎯 Provide intelligent next-step recommendations
- 🆕 Automatically start a new session with complete continuity
- ⚡ Use cached information for instant results

### Ending Your Claude Code Session

**ALWAYS run this when you're done working:**

```bash
mcp__fk-knowledge__endsession(reason="work_complete")
```

This will:
- ⏳ Wait for all data ingestion to complete (up to 30s)
- 📤 Export your session context as a searchable document
- 💾 Prepare resume information for your next session
- 🔄 Update all databases with final session state
- 🧹 Perform cleanup verification before shutdown

### Session Management Commands

```bash
# Quick session resume (uses cache)
mcp__fk-knowledge__resume_session(quick_summary=true)

# Full context resume (bypasses cache)
mcp__fk-knowledge__resume_session(quick_summary=false)

# End session with custom reason
mcp__fk-knowledge__endsession(reason="debugging_complete")

# End session with extended timeout
mcp__fk-knowledge__endsession(completion_timeout=60)
```

**Why This Matters:**
- 🧠 **Perfect Memory**: Never lose context between sessions
- 🎯 **Intelligent Resumption**: Always know exactly where you left off
- 📚 **Searchable History**: Every session is fully preserved and searchable
- 🔄 **Seamless Continuity**: Smooth transition between work sessions

**See `docs/SESSION_CONTINUITY_SYSTEM.md` for complete details.**

## Key Configuration

### Service URLs (Local Development)

- **FastAPI Backend**: http://localhost:8000 (API docs: /docs)
- **Frontend**: http://localhost:3000 (React application)
- **n8n**: http://localhost:5678 (admin/finderskeepers2025) - DEPRECATED
- **Neo4j Browser**: http://localhost:7474 (neo4j/fk2025neo4j)
- **Qdrant Dashboard**: http://localhost:6333

### Environment Variables Required

- `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY` - AI service keys
- `POSTGRES_PASSWORD=fk2025secure` - Database password
- `NEO4J_PASSWORD=fk2025neo4j` - Neo4j password

## Common Issues

### Port Conflicts

Check for conflicts on ports 5432, 5678, 6333, 6379, 7474, 7687, 8000

### Database Connection Issues

- Reset: `docker compose down -v && docker compose up -d`
- Check logs: `docker compose logs postgres`

### Memory Issues

- Minimum 8GB RAM recommended
- Adjust memory limits in `docker-compose.yml`

## Docker Authentication & Monitoring

### Docker Registry Login

```bash
# Docker credentials are in .env file (DOCKER_USERNAME, DOCKER_TOKEN)
# Use environment variables instead of docker login due to pass store issues:
export DOCKER_USERNAME=bitcainnet
export DOCKER_TOKEN=your_docker_token_from_env
```

### Portainer Docker Monitoring

```bash
# Install Portainer for visual Docker monitoring:
docker volume create portainer_data
docker run -d -p 8080:8000 -p 9443:9443 --name portainer --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data \
  portainer/portainer-ce:latest

# Access: http://localhost:9443 (HTTPS) or http://localhost:8080 (HTTP)
```

## Code Quality & Package Management

### Python Backend (services/diary-api/)
- **Python Version**: 3.12+
- **Package Manager**: `uv` (preferred) or `pip`
- **Code Style**: Black (88 char line length) + isort
- **Dependencies**: Managed via `pyproject.toml`
- **Testing**: pytest with asyncio support

### Frontend (fk2_frontend/)
- **Framework**: React 18 + TypeScript 5.7+
- **Build Tool**: Vite
- **Styling**: TailwindCSS + Material-UI
- **State**: Zustand
- **Linting**: ESLint with TypeScript rules

### Task Completion Checklist
Always run before considering a task complete:
```bash
# Backend
cd services/diary-api && uv run black . && uv run isort .

# Frontend  
cd fk2_frontend && npm run lint

# Health check
./scripts/health.sh
```

## File Structure Notes

- `services/diary-api/` - FastAPI application (Python 3.12+)
- `services/mcp-session-server/` - MCP server for Claude Desktop integration
- `fk2_frontend/` - React TypeScript frontend with Material-UI
- `config/` - Service configuration files
- `data/` - Persistent data storage (git-ignored)
- `logs/` - Application logs
- `scripts/` - Management and deployment scripts