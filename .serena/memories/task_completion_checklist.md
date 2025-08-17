# Task Completion Checklist

## When Task is Complete, Always Run:

### Code Quality Checks
```bash
# Backend (FastAPI)
cd services/diary-api
uv run black .  # Format code
uv run isort .  # Sort imports

# Frontend 
cd fk2_frontend
npm run lint  # Lint TypeScript/React code
```

### Testing
```bash
# Backend tests (when available)
cd services/diary-api  
uv run pytest

# Frontend tests (when available)
cd fk2_frontend
npm test
```

### Health Verification
```bash
# Check all services are running properly
./scripts/health.sh

# Verify specific endpoints
curl http://localhost:8000/docs  # FastAPI docs
curl http://localhost:3000       # Frontend
curl http://localhost:6333/collections  # Qdrant
```

### Docker Health Check
```bash
# Ensure all containers are healthy
docker compose ps

# Check resource usage
docker stats --no-stream
```

## Before Committing
1. Run all code quality checks above
2. Ensure Docker services start cleanly: `docker compose up -d`
3. Verify no breaking changes to API endpoints
4. Test MCP server functionality if changes affect session management
5. Check that frontend builds successfully: `npm run build`

## Deployment Verification
- All environment variables properly set in `.env`
- Database migrations applied if schema changes made
- No hardcoded credentials or API keys in code
- Docker images build without errors
- Background processing starts automatically after service startup

## Important Notes
- Backend uses `uv` as package manager (preferred over pip)
- Frontend dependencies managed in Docker volume `fk2_frontend_node_modules`
- MCP server runs separately from main Docker services
- Automatic background processing starts 30 seconds after FastAPI container startup