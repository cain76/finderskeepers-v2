# FindersKeepers v2 - AI-Powered Knowledge Management System

## Overview
FindersKeepers v2 is a comprehensive knowledge management system with persistent AI memory, vector search, and knowledge graph capabilities. Built for bitcain.net with RTX 2080 Ti GPU acceleration.

## Features
- 🧠 **AI GOD MODE**: Persistent memory across sessions
- 🔍 **Vector Search**: Real semantic search with Qdrant
- 🕸️ **Knowledge Graph**: Neo4j relationship mapping
- 📝 **Automatic Processing**: Background document pipeline
- 🤖 **Local LLM**: Llama3 8B + mxbai embeddings
- 🔄 **MCP Integration**: Direct Claude Desktop support

## Quick Start

### Prerequisites
- Docker & Docker Compose v2
- NVIDIA GPU with CUDA (RTX 2080 Ti recommended)
- 16GB+ RAM
- 50GB+ disk space

### Installation

1. Clone repository:
```bash
git clone https://github.com/bitcainnet/finderskeepers-v2.git
cd finderskeepers-v2
```

2. Create shared Docker network:
```bash
./ensure-network.sh
# or manually:
docker network create shared-network
```

3. Start services:
```bash
docker compose up -d
```

4. Wait for initialization (~5 minutes for model downloads)

5. Verify health:
```bash
./scripts/health.sh
```

### Access Points
- FastAPI: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Neo4j: http://localhost:7474
- Qdrant: http://localhost:6333

## MCP Server Setup (Claude Desktop)

Add to Claude Desktop config:
```json
{
  "mcpServers": {
    "fk2-mcp": {
      "command": "/path/to/project/.venv/bin/python",
      "args": ["src/fk2_mcp_server.py"],
      "env": {
        "POSTGRES_URL": "postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2",
        "FASTAPI_URL": "http://localhost:8000",
        "QDRANT_URL": "http://localhost:6333",
        "NEO4J_URL": "bolt://localhost:7687"
      }
    }
  }
}
```

## Configuration

### Environment Variables
Create `.env` file:
```env
DOCKER_USERNAME=your_username
DOCKER_TOKEN=your_token
OPENAI_API_KEY=optional_fallback
```

### Automatic Processing
Background processor runs every 5 minutes, processing 10 documents per batch. Configure in docker-compose.yml:
```yaml
FK2_ENABLE_BACKGROUND_PROCESSING=true
FK2_PROCESSING_INTERVAL_MINUTES=5
FK2_PROCESSING_BATCH_SIZE=10
```

## Troubleshooting

### Common Issues

**Vector search returns no results:**
- Check Qdrant is running: `docker ps | grep qdrant`
- Verify collection exists: `curl http://localhost:6333/collections`

**MCP tools not working:**
- Restart MCP server in Claude Desktop
- Check FastAPI health: `curl http://localhost:8000/api/mcp/health`

**Memory issues:**
- Reduce Ollama models: `docker exec fk2_ollama ollama rm llama3:8b`
- Lower batch sizes in configuration

### Logs
```bash
docker compose logs -f fastapi    # API logs
docker compose logs -f postgres   # Database logs
docker compose logs -f ollama     # LLM logs
```

## Development

### Project Structure
```
finderskeepers-v2/
├── services/
│   ├── diary-api/          # FastAPI backend
│   ├── mcp-session-server/ # MCP server
│   └── crawl4ai-service/   # Web scraper
├── frontend/               # React UI
├── scripts/               # Utilities
└── docker-compose.yml     # Service orchestration
```

### Key Technologies
- **Backend**: FastAPI, PostgreSQL (pgvector), Neo4j, Qdrant
- **AI/ML**: Ollama, Llama3 8B, mxbai-embed-large
- **Frontend**: React, Vite
- **Infrastructure**: Docker, NVIDIA CUDA

## License
MIT License - See LICENSE file

## Support
- GitHub Issues: https://github.com/bitcainnet/finderskeepers-v2
- Documentation: /docs/API_DOCUMENTATION.md

## Credits
Created by bitcain.net for advanced AI knowledge management.
