# FindersKeepers v2 - Container Communication Fix Guide

## 🔧 Quick Fix Instructions

After the GitHub security updates broke container communication, use these scripts to completely rebuild your FindersKeepers v2 environment.

### Step 1: Run the Complete Rebuild Script

```bash
cd /media/cain/linux_storage/projects/finderskeepers-v2
./start-fk2-fixed.sh
```

This script will:
- ✅ Completely stop and remove all FK2 containers
- ✅ Recreate the Docker network with proper configuration
- ✅ Apply fixed IP addresses for reliable container communication
- ✅ Rebuild all services from scratch
- ✅ Initialize Ollama models (llama3:8b and mxbai-embed-large)
- ✅ Perform health checks on all services

### Step 2: Verify Communication

Run the diagnostic script to ensure all containers can communicate:

```bash
./diagnose-fk2.sh
```

This will test:
- PostgreSQL connectivity
- Redis connectivity  
- Qdrant vector database access
- Neo4j graph database access
- Ollama LLM service access
- MCP endpoints availability

### Step 3: Check MCP Server Integration

Test that the MCP server (for Claude Desktop) is working:

```bash
# Check MCP health
curl http://localhost:8000/api/mcp/health

# View recent sessions
curl http://localhost:8000/api/mcp/sessions/recent

# Check processing statistics
curl http://localhost:8000/api/v1/stats
```

## 🐛 What Was Fixed

### 1. **Network Configuration**
- Changed from dynamic Docker networking to fixed IP addresses
- Created `docker-compose.override.yml` to ensure consistent container addressing
- Fixed the external network configuration issue

### 2. **Service Discovery**
- FastAPI now uses container names (fk2_postgres, fk2_redis, etc.) for internal communication
- Added extra_hosts entries to ensure DNS resolution
- Fixed environment variables to use correct hostnames

### 3. **Container Dependencies**
- Proper health checks for PostgreSQL before starting dependent services
- Fixed startup order to prevent race conditions
- Added retry logic for service initialization

### 4. **Security Updates Compatibility**
- Removed deprecated n8n webhook dependencies
- Direct FastAPI integration for MCP server
- Background processing runs automatically without n8n

## 📊 Service Architecture

```
┌─────────────────────────────────────────────────────┐
│                   shared-network                     │
│                  (172.25.0.0/16)                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐        ┌──────────────┐          │
│  │  PostgreSQL  │        │    FastAPI   │          │
│  │ 172.25.0.10  │◄──────►│ 172.25.0.20  │          │
│  └──────────────┘        └──────────────┘          │
│         ▲                       ▲ ▼                 │
│         │                       │ │                 │
│  ┌──────────────┐        ┌──────────────┐          │
│  │    Neo4j     │        │    Qdrant    │          │
│  │ 172.25.0.11  │◄──────►│ 172.25.0.13  │          │
│  └──────────────┘        └──────────────┘          │
│         ▲                       ▲                   │
│         │                       │                   │
│  ┌──────────────┐        ┌──────────────┐          │
│  │    Redis     │        │    Ollama    │          │
│  │ 172.25.0.12  │◄──────►│ 172.25.0.14  │          │
│  └──────────────┘        └──────────────┘          │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## 🚀 Features Now Working

- ✅ **Automatic Document Processing**: Processes 10 documents every 5 minutes
- ✅ **MCP Session Management**: Full session persistence and resume capability
- ✅ **Vector Search**: Qdrant integration with 1024-dimensional embeddings
- ✅ **Knowledge Graph**: Neo4j entity extraction and relationship mapping
- ✅ **GPU Acceleration**: RTX 2080 Ti CUDA support for Ollama and vector operations
- ✅ **Admin Dashboard**: Bulk processing and queue management at http://localhost:3000/monitoring

## 🔍 Troubleshooting

### If containers still can't communicate:

1. **Check Docker network**:
```bash
docker network inspect shared-network
```

2. **Verify container IPs**:
```bash
docker compose exec fastapi cat /etc/hosts
```

3. **Check service logs**:
```bash
docker compose logs fastapi --tail 50
docker compose logs postgres --tail 50
```

4. **Complete reset** (WARNING: Deletes all data):
```bash
docker compose down -v
docker network rm shared-network
./start-fk2-fixed.sh
# Choose 'y' when prompted to delete volumes
```

### If MCP server isn't working:

1. **Check FastAPI is running**:
```bash
docker compose ps fastapi
```

2. **Verify MCP endpoints**:
```bash
curl -v http://localhost:8000/api/mcp/health
```

3. **Check Claude Desktop configuration** in `~/.config/claude/config.json`:
```json
{
  "mcpServers": {
    "fk2-mcp": {
      "command": "/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-session-server/.venv/bin/python",
      "args": [
        "/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-session-server/src/fk2_mcp_server.py"
      ],
      "env": {
        "FASTAPI_URL": "http://localhost:8000"
      }
    }
  }
}
```

## 📝 Environment Variables

Make sure your `.env` file has these critical settings:

```env
# Docker credentials
DOCKER_USERNAME=bitcainnet
DOCKER_TOKEN=<your_actual_token>

# Database passwords (change these!)
POSTGRES_PASSWORD=fk2025secure
NEO4J_PASSWORD=fk2025neo4j

# Timezone (for Chicago)
TZ=America/Chicago
TIMEZONE=America/Chicago

# Background processing
FK2_ENABLE_BACKGROUND_PROCESSING=true
FK2_PROCESSING_INTERVAL_MINUTES=5
```

## 🎯 One-Command Deploy

For deploying on another machine:

```bash
# Clone repository
git clone https://github.com/bitcain/finderskeepers-v2.git
cd finderskeepers-v2

# Copy environment file and edit
cp .env.example .env
nano .env  # Add your Docker token and change passwords

# Run the complete setup
./start-fk2-fixed.sh
```

The system will automatically:
- Create all required networks and volumes
- Pull and build all containers
- Initialize Ollama models
- Start background document processing
- Set up the admin dashboard

## 📞 Support

For issues specific to the bitcain.net infrastructure:
- Check logs: `docker compose logs -f`
- Run diagnostics: `./diagnose-fk2.sh`
- Verify GPU: `nvidia-smi`
- Monitor processing: `docker logs fk2_fastapi --tail 50 | grep Processing`

---

**Note**: This fix addresses the container communication issues that occurred after GitHub security updates. The system now uses fixed IP addresses and explicit container naming to ensure reliable inter-service communication.
