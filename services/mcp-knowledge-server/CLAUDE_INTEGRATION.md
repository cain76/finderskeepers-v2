# Claude Code Integration Guide

## Automatic Installation (Recommended)

Add this to your Claude Code `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "finderskeepers-knowledge": {
      "command": "/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/.venv/bin/python",
      "args": ["/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src/knowledge_server.py"],
      "env": {
        "PYTHONPATH": "/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src"
      }
    }
  }
}
```

## Manual Installation

1. Start the server manually:
```bash
/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/start-server.sh
```

2. In Claude Code, connect to the server:
```
/mcp connect stdio "/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/.venv/bin/python" "/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src/knowledge_server.py"
```

## Verification

Test the installation by asking Claude:
- "Search our knowledge base for Docker setup"
- "What do we know about session management?"
- "Show me recent project activity"

## Troubleshooting

1. **Database Connection Issues**: Verify services are running:
   ```bash
   docker-compose ps  # Check if PostgreSQL, Neo4j, Qdrant, Redis are running
   ```

2. **Environment Variables**: Check your `.env` file configuration

3. **Python Dependencies**: Reinstall if needed:
   ```bash
   /media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/.venv/bin/pip install -e /media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server
   ```

4. **Logs**: Check server logs for detailed error information

## Configuration

Edit `/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/.env` to configure:
- Database connection strings
- API keys for enhanced features  
- Logging levels and formats
- Session management timeouts
