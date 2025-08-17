# Essential Commands for FindersKeepers v2

## Service Management
```bash
# Start all services (recommended)
./scripts/start-all.sh

# Stop all services  
./scripts/stop-all.sh

# Start specific services
docker compose up -d postgres neo4j redis qdrant
docker compose up -d fastapi

# Health check
./scripts/health.sh

# View logs
docker compose logs -f
docker compose logs -f fastapi
```

## Development Environment
```bash
# Backend development (requires Docker services running)
cd services/diary-api
uv sync  # Install dependencies with uv
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend development
cd fk2_frontend
npm install
npm run dev  # Starts on port 3000

# Frontend linting
npm run lint
```

## Code Quality
```bash
# Python formatting (FastAPI backend)
cd services/diary-api
uv run black .
uv run isort .

# Frontend linting
cd fk2_frontend
npm run lint
```

## Testing
```bash
# Backend tests (when implemented)
cd services/diary-api
uv run pytest

# Frontend tests
cd fk2_frontend
npm test
```

## Database Operations
```bash
# PostgreSQL direct access
docker exec -it fk2_postgres psql -U finderskeepers -d finderskeepers_v2

# Neo4j browser access - http://localhost:7474 (neo4j/fk2025neo4j)

# Redis CLI
docker exec -it fk2_redis redis-cli

# Check Qdrant collections
curl http://localhost:6333/collections
```

## MCP Session Management
```bash
# MCP server (separate from main services)
cd services/mcp-knowledge-server
source .venv/bin/activate
python src/knowledge_server.py

# Clean up stuck MCP processes
./scripts/cleanup-mcp-sessions.sh

# Clean up zombie database sessions
./scripts/cleanup-zombie-sessions.py --dry-run
./scripts/cleanup-zombie-sessions.py --max-age 6 --force
```

## Docker Utilities
```bash
# Reset database volumes
docker compose down -v && docker compose up -d

# Remove frontend node_modules volume
./scripts/prune-frontend-node-modules.sh

# Check container resource usage
docker stats

# Container logs for debugging
docker compose logs postgres
docker compose logs neo4j
```