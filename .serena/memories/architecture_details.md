# FindersKeepers v2 Architecture Details

## Service Dependencies
```
Frontend (React) → FastAPI Backend
FastAPI Backend → PostgreSQL + pgvector
FastAPI Backend → Neo4j (Knowledge Graph)  
FastAPI Backend → Qdrant (Vector Search)
FastAPI Backend → Redis (Caching)
FastAPI Backend → Ollama (Local LLM)
MCP Server → FastAPI Backend (Direct API calls)
n8n → DEPRECATED (No longer used)
```

## Key Data Models
- **AgentSession**: Tracks individual AI agent interactions with JSONB context
- **AgentAction**: Logs specific actions within sessions (file edits, commands, etc.)
- **DocumentIngest**: Handles knowledge base document storage and indexing
- **KnowledgeQuery**: Natural language queries against the knowledge graph
- **ConfigChange**: Tracks system configuration changes with rollback capability

## API Architecture
### Core Endpoints
- `/api/diary/*` - Agent session tracking and history
- `/api/knowledge/*` - Natural language knowledge queries
- `/api/docs/*` - Document ingestion and context retrieval
- `/api/config/*` - Configuration change tracking
- `/api/mcp/*` - MCP server health and diagnostics

## Background Processing
- Automatic document processing starts 30 seconds after FastAPI startup
- Processes 10 documents per batch every 5 minutes
- No manual intervention required
- Handles document chunking, embedding generation, knowledge graph updates

## Storage Architecture
- **PostgreSQL**: Primary data store with vector embeddings (pgvector)
- **Neo4j**: Entity relationships and knowledge graph queries
- **Qdrant**: High-performance vector similarity search
- **Redis**: Session caching and temporary data
- **Docker Volumes**: Persistent data storage (`fk2_*` prefixed volumes)

## Network Architecture
- Shared Docker network: `shared-network`
- Internal service discovery via container names
- External access via mapped ports (3000, 5678, 6333, 7474, 8000)

## Security Model
- JWT authentication for API access
- bcrypt password hashing
- Docker secrets for sensitive configuration
- No hardcoded credentials (uses .env file)
- NVIDIA GPU access restricted to specific containers