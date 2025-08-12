# GitHub Copilot Instructions for FindersKeepers v2

**ALWAYS follow these instructions first and only fallback to additional search and context gathering if the information in the instructions is incomplete or found to be in error.**

FindersKeepers v2 is a personal AI agent knowledge hub built with a containerized microservices architecture. It tracks agent sessions, manages documentation, and provides intelligent knowledge retrieval across multiple AI interactions.

## Working Effectively

### Prerequisites and Setup
- Ensure Docker and Docker Compose v2 are installed and running
- Create `.env` file with minimal configuration:
```bash
# Copy this basic configuration to .env file
DOCKER_USERNAME=testuser
DOCKER_TOKEN=testtoken
POSTGRES_PASSWORD=fk2025secure
NEO4J_PASSWORD=fk2025neo4j
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=finderskeepers2025
```

### Core Development Workflow
1. **Start Database Services (Required First Step)**:
   ```bash
   # Create required Docker network
   docker network create shared-network || echo "Network already exists"
   
   # Start core database services - NEVER CANCEL: Takes 30-45 seconds
   docker compose up -d postgres redis neo4j qdrant
   ```
   - **Timeout: Set 120+ seconds** - Database initialization can take time
   - **NEVER CANCEL** - PostgreSQL, Neo4j initialization requires patience
   - Wait 30 seconds after startup before testing connections

2. **FastAPI Backend Development**:
   ```bash
   cd services/diary-api
   python3 -m venv .venv
   source .venv/bin/activate
   
   # Install core dependencies - Takes 15-20 seconds
   pip install fastapi uvicorn httpx pydantic python-dotenv
   
   # For full development with database integration:
   pip install asyncpg redis psutil pytest pytest-asyncio
   
   # Start development server
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   - **Timeout: Set 300+ seconds for pip install** - Full requirements.txt can take time
   - Development server starts in under 5 seconds with basic dependencies

3. **Frontend Development**:
   ```bash
   cd frontend
   
   # Install dependencies - NEVER CANCEL: Takes 60-90 seconds
   npm ci
   
   # Start development server - Starts in under 1 second
   npm run dev
   ```
   - **Timeout: Set 300+ seconds for npm ci** - Node.js dependencies are large
   - **NEVER CANCEL** npm operations - Let them complete fully
   - Development server available at http://localhost:3000

### Testing and Validation

1. **Run Unit Tests**:
   ```bash
   cd services/diary-api && source .venv/bin/activate
   python -m pytest -v --tb=short
   ```
   - Tests complete in under 5 seconds
   - Always run tests after making changes

2. **Validate Database Connectivity**:
   ```bash
   # Test all database endpoints
   curl -s http://localhost:6333/collections  # Qdrant
   curl -s http://localhost:7474             # Neo4j  
   docker exec fk2_redis redis-cli ping      # Redis
   docker exec fk2_postgres pg_isready -U finderskeepers  # PostgreSQL
   ```

3. **Health Check Script** (Always run after startup):
   ```bash
   ./scripts/health.sh
   ```
   - **Timeout: Set 180+ seconds** - Comprehensive health checks take time
   - **NEVER CANCEL** - Let all health checks complete

### Build and Deployment Timings

**Critical Timing Information:**
- **Docker image pull**: 45-60 seconds - NEVER CANCEL
- **Database service startup**: 30-45 seconds - NEVER CANCEL  
- **npm ci (frontend)**: 60-90 seconds - NEVER CANCEL
- **pip install (basic)**: 15-20 seconds
- **pip install (full requirements)**: 3-5 minutes - NEVER CANCEL
- **Test suite execution**: Under 10 seconds
- **Development servers startup**: Under 5 seconds

**Always set timeouts appropriately:**
- Build commands: 300+ seconds minimum
- Database operations: 180+ seconds minimum
- Package installations: 300+ seconds minimum

## Validation Scenarios

**ALWAYS test these complete user scenarios after making changes:**

### Scenario 1: Database Integration Test
```bash
# Prerequisites: All database services running
cd services/diary-api && source .venv/bin/activate

# Create test script to validate:
python -c "
import asyncio
import asyncpg
import redis
import httpx

async def test_integration():
    # Test PostgreSQL
    conn = await asyncpg.connect('postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2')
    result = await conn.fetchval('SELECT 1 + 1')
    await conn.close()
    assert result == 2, 'PostgreSQL integration failed'
    
    # Test Redis
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.set('test_key', 'test_value', ex=10)
    assert r.get('test_key') == 'test_value', 'Redis integration failed'
    r.delete('test_key')
    
    # Test Qdrant
    async with httpx.AsyncClient() as client:
        response = await client.get('http://localhost:6333/collections')
        assert response.status_code == 200, 'Qdrant integration failed'
    
    print('✅ All database integrations working')

asyncio.run(test_integration())
"
```

### Scenario 2: API Development Workflow Test
```bash
# Test FastAPI development workflow
cd services/diary-api && source .venv/bin/activate

# Create minimal test API
python -c "
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get('/health')
def health():
    return {'status': 'healthy'}

@app.get('/test')  
def test_endpoint():
    return {'message': 'API working', 'data': [1, 2, 3]}

# Test the API
client = TestClient(app)
response = client.get('/health')
assert response.status_code == 200
assert response.json()['status'] == 'healthy'

response = client.get('/test')
assert response.status_code == 200
assert 'message' in response.json()

print('✅ FastAPI development workflow working')
"
```

### Scenario 3: Frontend Integration Test
```bash
# Test frontend development server
cd frontend

# Start development server (background)
npm run dev &
DEV_PID=$!

# Wait for server to start
sleep 3

# Test frontend is serving
curl -s -f http://localhost:3000/ > /dev/null && echo "✅ Frontend development server working" || echo "❌ Frontend not responding"

# Cleanup
kill $DEV_PID
```

## Common Issues and Solutions

### Build Failures
**Issue**: SSL certificate errors during pip/npm install
**Solution**: This is common in CI environments. Document as expected limitation:
- "Build may fail in restricted network environments due to SSL certificate validation"
- "Local development with direct internet access works correctly"

### Database Connection Issues
**Issue**: "Connection refused" errors
**Solution**: 
```bash
# Reset all services
docker compose down -v
docker network create shared-network || true
docker compose up -d postgres redis neo4j qdrant
# Wait 30 seconds before testing connections
```

### Port Conflicts
**Issue**: "Port already in use" errors  
**Solution**: Check for conflicts on ports 3000, 5432, 6333, 6379, 7474, 7687, 8000
```bash
# Find processes using required ports
netstat -tulnp | grep -E ':(3000|5432|6333|6379|7474|7687|8000)'
```

### Memory Issues
**Issue**: Services crash or fail to start
**Solution**: Ensure minimum 4GB RAM available, 8GB+ recommended

## Key Project Structure

### Core Services
- **`services/diary-api/`** - FastAPI backend (Python 3.12)
  - Main API endpoints and business logic
  - Database integration and AI processing
  - Start development: `uvicorn main:app --reload`

- **`frontend/`** - React/Vite application  
  - User interface and admin dashboard
  - Real-time data visualization
  - Start development: `npm run dev`

- **`scripts/`** - Utility and management scripts
  - `health.sh` - Comprehensive system health check
  - `start-all.sh` - Complete system startup
  - `stop-all.sh` - Clean system shutdown

### Configuration Files
- **`docker-compose.yml`** - Production configuration (GPU-optimized)
- **`docker-compose.test.yml`** - Testing configuration (no GPU)
- **`.env`** - Environment variables and secrets
- **`pyproject.toml`** - Python project configuration
- **`package.json`** - Node.js dependencies and scripts

### Database Schema
- **PostgreSQL**: Core data storage with pgvector for embeddings
- **Neo4j**: Knowledge graph for entity relationships  
- **Qdrant**: High-performance vector search
- **Redis**: Caching and session management

## Frequent Commands Reference

```bash
# System Management
docker compose up -d                    # Start all services
docker compose down -v                  # Stop and clean all services  
docker compose logs -f [service]        # View service logs
./scripts/health.sh                     # Complete health check

# Development  
cd services/diary-api && source .venv/bin/activate  # Activate Python env
uvicorn main:app --reload                           # Start FastAPI dev server
cd frontend && npm run dev                          # Start frontend dev server

# Testing
python -m pytest -v                     # Run Python tests
npm run test                            # Run frontend tests (if available)
curl http://localhost:8000/docs         # Test API documentation
curl http://localhost:3000/             # Test frontend

# Database Access
docker exec -it fk2_postgres psql -U finderskeepers -d finderskeepers_v2
docker exec -it fk2_redis redis-cli
curl http://localhost:7474              # Neo4j browser  
curl http://localhost:6333/collections  # Qdrant collections
```

## Critical Warnings

- **NEVER CANCEL** long-running build or install operations
- **ALWAYS wait** 30+ seconds after starting databases before testing
- **NEVER use** `docker system prune` - it will remove required data volumes
- **ALWAYS set timeouts** of 300+ seconds for build operations  
- **TEST database connectivity** before running FastAPI application
- **VALIDATE all endpoints** after making API changes
- **RUN health checks** after any configuration changes

## Success Indicators

✅ **System is ready when:**
- All database services show "healthy" status in `docker compose ps`
- Health check script passes all tests
- API responds at http://localhost:8000/docs  
- Frontend loads at http://localhost:3000
- All ports (3000, 5432, 6333, 6379, 7474, 7687, 8000) are accessible

✅ **Development workflow is working when:**
- Python virtual environment activates successfully
- FastAPI development server starts without errors
- Frontend development server starts in under 1 second
- All integration tests pass
- Database connections can be established programmatically