# MCP INSTALL COMMANDS FOR CLAUDE CODE

## 🚨 IMPORTANT: Install Order and Environment Setup

**Execute these commands in order. Test each one before proceeding to the next.**

### Environment Variables Setup (Run First)
```bash
# Export environment variables for MCP servers
export BRAVE_API_KEY="BSAomC2D07-YMgcFrMPAMQOpCMCI0CP"
export KUBECONFIG="/home/cain/.kube/config"
export POSTGRES_URL="postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2"
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="fk2025neo4j"
export QDRANT_URL="http://localhost:6333"
export REDIS_URL="redis://localhost:6379"
export FASTAPI_URL="http://localhost:8000"
```

---

## 📋 ESSENTIAL USER-SCOPE SERVERS (Install First)

### 1. Filesystem Access (PRIORITY 1)
```bash
claude mcp add --scope=user filesystem npx @modelcontextprotocol/server-filesystem /home /media/cain/linux_storage
```

### 2. IDE Integration 
```bash
claude mcp add --scope=user ide npx -y @jitl/mcp-server-code
```

### 3. Web Search (with API key)
```bash
claude mcp add-json --scope=user brave-search '{
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-brave-search"],
  "env": {
    "BRAVE_API_KEY": "BSAomC2D07-YMgcFrMPAMQOpCMCI0CP"
  }
}'
```

### 4. Sequential Thinking
```bash
claude mcp add --scope=user sequential-thinking npx -y @modelcontextprotocol/server-sequential-thinking
```

### 5. Context Management
```bash
claude mcp add --scope=user context7 npx -y @upstash/context7-mcp
```

### 6. Think MCP
```bash
claude mcp add --scope=user think-mcp npx -y think-mcp
```

### 7. Web Fetch Tools
```bash
claude mcp add --scope=user fetch npx -y @modelcontextprotocol/server-fetch
```

### 8. Desktop Commander
```bash
claude mcp add --scope=user desktop-commander npx -y @wonderwhy-er/desktop-commander
```

### 9. Puppeteer Browser Automation
```bash
claude mcp add --scope=user puppeteer_tools npx -y puppeteer-mcp-server
```

---

## 🔧 ADVANCED USER-SCOPE SERVERS (Optional)

### 10. Firecrawl (Requires FIRECRAWL_API_KEY)
```bash
# Note: Set FIRECRAWL_API_KEY environment variable first
claude mcp add-json --scope=user mcp-server-firecrawl '{
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@firecrawl/mcp-server-firecrawl"],
  "env": {
    "FIRECRAWL_API_KEY": "${FIRECRAWL_API_KEY}"
  }
}'
```

### 11. Cloudflare Observability (SSE)
```bash
claude mcp add --transport sse --scope=user cloudflare-observability https://observability.mcp.cloudflare.com/sse
```

### 12. Cloudflare Bindings (SSE)
```bash
claude mcp add --transport sse --scope=user cloudflare-bindings https://bindings.mcp.cloudflare.com/sse
```

---

### 9. FindersKeepers Knowledge Server (GLOBAL - Available Everywhere)
```bash
# Install as USER-SCOPE so it's available in ALL projects
claude mcp add-json --scope=user fk-knowledge '{
  "type": "stdio",
  "command": "/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/.venv/bin/python",
  "args": ["/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src/knowledge_server.py"],
  "env": {
    "POSTGRES_URL": "postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2",
    "NEO4J_URI": "bolt://localhost:7687",
    "NEO4J_USER": "neo4j",
    "NEO4J_PASSWORD": "fk2025neo4j",
    "QDRANT_URL": "http://localhost:6333",
    "REDIS_URL": "redis://localhost:6379",
    "FASTAPI_URL": "http://localhost:8000",
    "CRASH_RECOVERY_ENABLED": "true",
    "BULLETPROOF_MODE": "true",
    "AUTO_SESSION_LOGGING": "true",
    "BACKUP_PERSISTENCE": "maximum"
  }
}'
```

**🌍 Why User Scope for fk-knowledge:**
- **Global Access**: Available across ALL your projects, not just finderskeepers-v2
- **Docker Integration**: Connects to your containerized services (PostgreSQL, Neo4j, Qdrant, Redis) via localhost
- **Universal Knowledge Hub**: Acts as your personal AI knowledge assistant for any coding project
- **Persistent Resources**: Always connects to the same running Docker containers regardless of current directory

### 13. Crawl4AI (Custom Implementation)
```bash
claude mcp add --scope=project crawl4ai /media/cain/linux_storage/bitcain/crawl4ai-mcp-server/run_mcp_safe.sh
```

---

## ☸️ INFRASTRUCTURE SERVERS (Advanced/Optional)

### 14. Kubernetes Management
```bash
claude mcp add-json --scope=user kubernetes '{
  "type": "stdio",
  "command": "node",
  "args": ["/media/cain/linux_storage/projects/finderskeepers-v2/node_modules/mcp-server-kubernetes/dist/index.js"],
  "env": {
    "KUBECONFIG": "/home/cain/.kube/config"
  }
}'
```

---

## 🔍 VERIFICATION COMMANDS

After installing servers, verify they are working:

```bash
# List all installed MCP servers
claude mcp list

# Check specific scope
claude mcp list --scope=user
claude mcp list --scope=project

# Start Claude and check MCP status
claude
/mcp  # In Claude CLI to see active servers
```

---

## ⚙️ PROJECT SETTINGS CONFIGURATION

Create/update `.claude/settings.json` in your project:

```json
{
  "enableAllProjectMcpServers": false,
  "enabledMcpjsonServers": [
    "crawl4ai"
  ],
  "disabledMcpjsonServers": []
}
```

---

## 🚨 TROUBLESHOOTING

### Common Issues:

1. **Server won't start**: Check paths are absolute and files exist
2. **Permission denied**: Ensure scripts are executable
3. **Environment variables**: Source your .env files first
4. **Database connections**: Ensure services are running

### Debug Commands:
```bash
# Start Claude with MCP debugging
claude --mcp-debug

# Test server manually
npx @modelcontextprotocol/server-filesystem /home

# Check environment variables
env | grep -E "(BRAVE|N8N|POSTGRES|NEO4J)"
```

---

## 📝 NOTES

- **Install Order**: User scope first, then project scope
- **Test Each**: Restart Claude and test `/mcp` after each installation
- **Environment**: Source `.env` files in your shell before running commands
- **Paths**: All paths are absolute to prevent issues
- **Security**: API keys are included but consider using environment variables in production

**Remember**: These commands recreate your exact previous MCP server configuration. Install them gradually and test each one!