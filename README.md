# 🔍 FindersKeepers v2: Personal AI Agent Knowledge Hub

**Your Digital Memory & Project Documentation Center**

A containerized, scalable knowledge management system designed for AI agents to share memories, track project history, and maintain institutional knowledge across sessions.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM recommended
- 50GB+ disk space

### 1. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
```

### 2. Launch All Services
```bash
# Start everything (first time may take 5-10 minutes)
docker-compose up -d

# Check status
docker-compose ps
```

### 3. Access Points
- **n8n Workflows**: http://localhost:5678 (admin/finderskeepers2025)
- **FastAPI Docs**: http://localhost:8000/docs  
- **Neo4j Browser**: http://localhost:7474 (neo4j/fk2025neo4j)
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## 🏗️ Architecture

### Core Services
- **n8n** (Port 5678) - Workflow automation for agent coordination
- **FastAPI** (Port 8000) - API backend for diary/documentation  
- **PostgreSQL+pgvector** (Port 5432) - Vector embeddings & relational data
- **Qdrant** (Port 6333) - High-performance vector search
- **Neo4j** (Port 7474/7687) - Knowledge graph relationships
- **Redis** (Port 6379) - Caching & session management

### Data Persistence
All data is stored in `./data/` with automatic backups:
```
data/
├── postgres-data/     # Vector embeddings & documents
├── neo4j-data/        # Knowledge graph
├── qdrant-data/       # High-speed vector search
├── redis-data/        # Cache & sessions
├── n8n-data/          # Workflow definitions
└── documents/         # Raw document storage
```

## 🧠 Key Features

### 🤖 Agent Session Logging
- Auto-capture every AI interaction with timestamp and context
- Track file changes, commands executed, configuration updates
- Cross-reference between different AI agents (Claude, GPT, etc.)

### 📚 Project Documentation Hub  
- Centralized storage for all project docs (Bitcain, Skellekey, etc.)
- Auto-ingestion of README updates and documentation changes
- Context-aware document retrieval

### 🔧 Configuration Intelligence
- Track all configuration changes with impact analysis
- Smart recommendations based on historical performance
- One-click rollback to last working state

### 💬 Knowledge Chat Interface
- Direct conversation with your accumulated knowledge
- "What did we accomplish yesterday?" with full context
- Project-aware responses (knows if you're working on Bitcain vs Skellekey)

## ⚙️ Configuration Files

### Environment Variables (.env)
```bash
# AI API Keys
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key  
ANTHROPIC_API_KEY=your_anthropic_key

# n8n JWT Secret (provided in docker-compose.yml)
N8N_JWT_SECRET=provided_in_compose

# Database Passwords (auto-configured)
POSTGRES_PASSWORD=fk2025secure
NEO4J_PASSWORD=fk2025neo4j
```

## 🔧 Management Scripts

### Start/Stop Services
```bash
# Start all services
./scripts/start-all.sh

# Stop all services  
./scripts/stop-all.sh

# Restart specific service
docker-compose restart fastapi
```

### Data Management
```bash
# Backup all databases
./scripts/backup-data.sh

# Restore from backup
./scripts/restore-data.sh

# Import existing FindersKeepers data
./scripts/migrate-from-v1.sh
```

### Monitoring & Logs
```bash
# View all logs
docker-compose logs -f

# Specific service logs
docker-compose logs -f fastapi

# System status
docker-compose ps
docker stats
```

## 🔌 API Endpoints

### Diary System
```bash
# Log agent session
POST /api/diary/sessions

# Search session history  
GET /api/diary/search?q=docker&project=bitcain

# Get session context
GET /api/diary/context?session_id=123
```

### Knowledge Management
```bash
# Ask knowledge graph
POST /api/knowledge/query
{"question": "How do we deploy to Cloudflare?"}

# Store project documentation
POST /api/docs/ingest
{"content": "...", "project": "bitcain", "type": "procedure"}

# Get project context
GET /api/docs/context?project=bitcain&topic=docker
```

### Configuration Tracking
```bash
# Log configuration change
POST /api/config/log-change
{"change": "switched to OpenAI", "reason": "rate limits", "impact": "improved"}

# Get configuration history
GET /api/config/history?component=llm_provider

# Rollback configuration
POST /api/config/rollback?to_version=abc123
```

## 🚨 Troubleshooting

### Port Conflicts
```bash
# Check port usage
sudo lsof -i :5678
sudo lsof -i :8000

# Change ports in docker-compose.yml if needed
```

### Database Connection Issues
```bash
# Reset databases
docker-compose down -v
docker-compose up -d

# Check database logs
docker-compose logs postgres
docker-compose logs neo4j
```

### Memory Issues
```bash
# Check resource usage
docker stats

# Reduce memory limits in docker-compose.yml
# Or increase system RAM/swap
```

### Service Won't Start
```bash
# Check service status
docker-compose ps

# View error logs
docker-compose logs [service-name]

# Restart individual service
docker-compose restart [service-name]
```

## 📈 Scaling & Performance

### Resource Requirements
- **Minimum**: 4GB RAM, 2 CPU cores
- **Recommended**: 8GB RAM, 4 CPU cores  
- **Production**: 16GB RAM, 8 CPU cores

### Performance Tuning
- Adjust memory limits in docker-compose.yml
- Configure vector database index settings
- Enable connection pooling for high-traffic APIs

## 🔄 Migration from FindersKeepers v1

### Data Export
```bash
# From original FindersKeepers directory
python export_data.py --output /path/to/export.json
```

### Data Import  
```bash
# In FindersKeepers v2 directory
./scripts/import-v1-data.sh /path/to/export.json
```

## 🤝 Integration

### MCP Knowledge Server (New!)
**One-Command Installation for AI Agents**

```bash
# Automated installation with all dependencies
./services/mcp-knowledge-server/install.sh

# For development environment
./services/mcp-knowledge-server/install.sh --dev
```

**Features:**
- 🧠 **Semantic Knowledge Search** - Natural language access to your knowledge base
- 🔄 **Robust Session Management** - Multi-layer termination with crash recovery  
- 🚪 **Graceful Exit Commands** - Type `/exit` for clean shutdowns
- 💓 **Heartbeat Monitoring** - 90-second crash detection
- 🛡️ **Database Fallback** - Never lose sessions due to webhook failures
- 📝 **Conversation Tracking** - Complete interaction history

**Claude Code Integration:**
```json
{
  "mcpServers": {
    "finderskeepers-knowledge": {
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/src/knowledge_server.py"]
    }
  }
}
```

**Usage Examples:**
```
"Search our knowledge base for Docker GPU setup"
"What do we know about FastAPI authentication?"  
"Show me recent agent activity for this project"
"/exit" # Graceful session termination
```

### n8n Workflow Examples
- Auto-log Claude sessions → Knowledge graph
- Monitor project directories → Auto-ingest docs
- Configuration change alerts → Slack notifications
- Daily knowledge summaries → Email reports

## 🛡️ Security

### Local-First Design
- All data stays on your machine
- No external dependencies for core functionality
- API keys stored in environment variables only

### Network Security
- Services isolated in Docker network
- No external ports exposed except defined ones
- Redis and databases accessible only within network

## 📋 Roadmap

- [x] ✅ **Docker containerization** (COMPLETE)
- [x] ✅ **FastAPI backend with diary endpoints** (COMPLETE)  
- [x] ✅ **MCP Knowledge Server with robust session management** (COMPLETE)
- [x] ✅ **Multi-layer session termination & crash recovery** (COMPLETE)
- [x] ✅ **Automated deployment system** (COMPLETE)
- [ ] 🚧 **n8n workflows for agent automation** (IN PROGRESS)
- [ ] 📝 **Web chat interface**
- [ ] 🤖 **Advanced AI agent coordination**
- [ ] 📱 **Mobile companion app** (future)
- [ ] 🔄 **Real-time collaboration features**

---

**FindersKeepers v2: Where AI agents share memories and humans never lose context! 🔍➡️🧠**