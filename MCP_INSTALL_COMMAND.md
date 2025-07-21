# FindersKeepers v2 MCP Knowledge Server Installation

## One-Line Installation Command

```bash
claude mcp add fk-knowledge stdio "/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/.venv/bin/python" "/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src/knowledge_server.py" --env PYTHONPATH="/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src" --env POSTGRES_URL="postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2" --env NEO4J_URL="bolt://localhost:7687" --env NEO4J_USER="neo4j" --env NEO4J_PASSWORD="fk2025neo4j" --env REDIS_URL="redis://localhost:6379" --env QDRANT_URL="http://localhost:6333" --env FASTAPI_URL="http://localhost:8000" --env N8N_WEBHOOK_URL="http://localhost:5678"
```

## Prerequisites

Before running the installation command, ensure:

1. **Docker services are running**:
   ```bash
   docker compose up -d postgres neo4j redis qdrant
   ```

2. **Python virtual environment is set up**:
   ```bash
   cd /media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **FastAPI service is running**:
   ```bash
   cd /media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Verification

After installation, verify the MCP server is working:

```bash
claude mcp list
```

The `fk-knowledge` server should be listed and available.

## Removal (if needed)

To remove the MCP server:

```bash
claude mcp remove fk-knowledge
```