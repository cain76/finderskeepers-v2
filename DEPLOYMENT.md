# FindersKeepers v2 - Deployment Guide

Complete guide for deploying FindersKeepers v2 MCP Knowledge Server on new clients.

## 🚀 Quick Installation

### Option 1: Automated Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/finderskeepers-v2.git
cd finderskeepers-v2

# Run the automated installer
./services/mcp-knowledge-server/install.sh

# For development environment with testing tools
./services/mcp-knowledge-server/install.sh --dev
```

### Option 2: Manual Installation

```bash
# 1. Navigate to the MCP server directory
cd services/mcp-knowledge-server

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -e .

# 4. Copy and configure environment
cp .env.template .env
# Edit .env with your database credentials

# 5. Start the server
./start-server.sh
```

## 📋 Prerequisites

### System Requirements
- **Python**: 3.11 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Storage**: 1GB free space

### Required Services
The MCP Knowledge Server connects to these services:

1. **PostgreSQL** (with pgvector extension)
2. **Neo4j** (graph database)
3. **Qdrant** (vector search)
4. **Redis** (caching)
5. **FastAPI Backend** (FindersKeepers v2 API)

### Docker Setup (Recommended)
```bash
# Start all required services
docker-compose up -d postgres neo4j qdrant redis fastapi

# Verify services are running
docker-compose ps
```

## ⚙️ Configuration

### Environment Variables

Edit `.env` file with your specific configuration:

```bash
# Database Connections
POSTGRES_URL=postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2
NEO4J_URL=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=fk2025neo4j
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379

# API Endpoints
FASTAPI_URL=http://localhost:8000
N8N_WEBHOOK_URL=http://localhost:5678

# AI API Keys (optional)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### Network Configuration

Default ports used:
- **PostgreSQL**: 5432
- **Neo4j**: 7474 (HTTP), 7687 (Bolt)
- **Qdrant**: 6333
- **Redis**: 6379
- **FastAPI**: 8000
- **n8n**: 5678

## 🔗 Claude Code Integration

### Automatic Integration

Add to your `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "finderskeepers-knowledge": {
      "command": "/path/to/finderskeepers-v2/services/mcp-knowledge-server/.venv/bin/python",
      "args": ["/path/to/finderskeepers-v2/services/mcp-knowledge-server/src/knowledge_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/finderskeepers-v2/services/mcp-knowledge-server/src"
      }
    }
  }
}
```

### Manual Connection

```bash
# In Claude Code
/mcp connect stdio "/path/to/.venv/bin/python" "/path/to/src/knowledge_server.py"
```

## 🧪 Testing Installation

### Basic Connection Test

```bash
# Run the connection test script
.venv/bin/python test-connection.py
```

### Comprehensive Test Suite

```bash
# Test all session termination features
.venv/bin/python ../../scripts/test-session-termination.py
```

### Manual Testing in Claude Code

Try these commands:
```
"Search our knowledge base for Docker setup"
"What do we know about session management?"
"Show me recent project activity"
"/exit"  # Test graceful shutdown
```

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check if services are running
   docker-compose ps
   
   # Restart services
   docker-compose restart postgres neo4j qdrant redis
   ```

2. **Python Import Errors**
   ```bash
   # Reinstall dependencies
   source .venv/bin/activate
   pip install --upgrade -e .
   ```

3. **Permission Issues**
   ```bash
   # Fix script permissions
   chmod +x install.sh start-server.sh
   ```

4. **Environment Variable Issues**
   ```bash
   # Verify .env file exists and is properly formatted
   cat .env | grep -v '^#' | grep '='
   ```

### Log Analysis

Check logs for detailed error information:
```bash
# Server logs
tail -f logs/mcp-knowledge-server.log

# Docker service logs
docker-compose logs -f postgres
docker-compose logs -f neo4j
```

### Health Check

```bash
# Test individual database connections
.venv/bin/python -c "
import asyncio
from src.database.postgres_client import PostgresClient
asyncio.run(PostgresClient().health_check())
"
```

## 🚀 Production Deployment

### Security Considerations

1. **Environment Variables**: Use secure secret management
2. **Database Passwords**: Generate strong, unique passwords
3. **Network Security**: Configure firewalls and VPNs
4. **SSL/TLS**: Enable encryption for database connections

### Performance Optimization

1. **Database Tuning**: Optimize PostgreSQL and Neo4j configurations
2. **Connection Pooling**: Configure appropriate pool sizes
3. **Caching**: Utilize Redis for frequently accessed data
4. **Monitoring**: Set up health checks and alerting

### Scaling

1. **Horizontal Scaling**: Multiple MCP server instances
2. **Database Clustering**: Distribute database load
3. **Load Balancing**: Route requests across instances
4. **Auto-scaling**: Dynamic resource allocation

## 📁 Directory Structure

```
finderskeepers-v2/
├── services/mcp-knowledge-server/
│   ├── src/
│   │   ├── knowledge_server.py      # Main server
│   │   ├── activity_logger.py       # Session management
│   │   ├── conversation_monitor.py  # Exit detection
│   │   └── database/               # Database clients
│   ├── .venv/                      # Virtual environment
│   ├── .env                        # Configuration
│   ├── install.sh                  # Installer script
│   ├── start-server.sh            # Startup script
│   ├── pyproject.toml             # Dependencies
│   └── README.md                  # Documentation
```

## 🆘 Support

### Getting Help

1. **Documentation**: Check README files and inline comments
2. **Logs**: Review server and database logs
3. **Test Scripts**: Use provided testing utilities
4. **GitHub Issues**: Report bugs and feature requests

### Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request with detailed description

## 📊 Monitoring

### Health Checks

```bash
# Server health
curl http://localhost:8000/health

# Database health
.venv/bin/python test-connection.py
```

### Performance Metrics

- Session creation/termination rates
- Database query response times
- Memory and CPU usage
- Active connection counts

### Alerting

Set up monitoring for:
- Database connection failures
- High error rates
- Resource exhaustion
- Session timeout issues

## 🔄 Updates

### Updating the Server

```bash
# Pull latest changes
git pull origin master

# Update dependencies
source .venv/bin/activate
pip install --upgrade -e .

# Restart server
./start-server.sh
```

### Database Migrations

```bash
# Run database schema updates
./scripts/migrate-database.sh
```

This deployment guide ensures reliable, secure, and scalable installation of the FindersKeepers v2 MCP Knowledge Server across different environments.