# **COMPREHENSIVE MCP SERVER INSTALLATION GUIDE FOR CLAUDE CODE**

## **🚨 CRITICAL UNDERSTANDING: Configuration File Hierarchy**

**Claude Code uses THREE different scopes for MCP servers, each with different config files:**

1. **USER SCOPE** (Global): `~/.claude.json` - Available across ALL projects
2. **PROJECT SCOPE** (Shared): `.mcp.json` - Shared with team, committed to repo
3. **LOCAL SCOPE** (Personal): Stored in `.claude.json` per-project - Personal only

**⚠️ CONFLICT RESOLUTION ORDER**: Local → Project → User (most specific wins)

---

## **📁 CONFIGURATION FILE LOCATIONS & PURPOSES**

### **1. User-Scoped Configuration**
- **File**: `~/.claude.json`
- **Purpose**: MCP servers available across ALL your projects
- **Use Cases**: 
  - Personal productivity tools (filesystem, brave-search)
  - Development utilities you use everywhere
  - API integrations for your personal accounts

### **2. Project-Scoped Configuration**
- **File**: `<project-root>/.mcp.json`
- **Purpose**: MCP servers shared with your team
- **Use Cases**:
  - Project-specific tools (database connections, project APIs)
  - Team collaboration tools
  - Deployment/CI-CD integrations

### **3. Local Project Settings**
- **File**: `<project-root>/.claude/settings.json` or `<project-root>/.claude/settings.local.json`
- **Purpose**: Control which project MCP servers you personally enable/disable
- **Critical Settings**:
  ```json
  {
    "enableAllProjectMcpServers": false,  // 🚨 NEVER set to true unless you trust all project servers
    "enabledMcpjsonServers": ["server1", "server2"],  // Explicit allow list
    "disabledMcpjsonServers": ["unwanted-server"]     // Explicit deny list
  }
  ```

---

## **🔧 INSTALLATION METHODS**

### **Method 1: CLI Commands (RECOMMENDED)**

#### **Add User-Scoped Server (Available Everywhere)**
```bash
# Basic stdio server
claude mcp add --scope=user <server-name> <command> [args...]

# Example: Filesystem access
claude mcp add --scope=user filesystem npx @modelcontextprotocol/server-filesystem /home /media/cain/linux_storage

# Example: Brave search
claude mcp add --scope=user brave-search npx @modelcontextprotocol/server-brave-search
```

#### **Add Project-Scoped Server (Team Shared)**
```bash
# Add to project .mcp.json (gets committed)
claude mcp add --scope=project <server-name> <command> [args...]

# Example: Project-specific knowledge server
claude mcp add --scope=project fk-knowledge python services/mcp-knowledge-server/src/knowledge_server.py
```

#### **Add Local-Scoped Server (Personal Project)**
```bash
# Default scope - personal to you in this project only
claude mcp add <server-name> <command> [args...]

# Example: Development tools for this project only
claude mcp add --scope=local dev-tools npx @some/dev-tool
```

### **Method 2: JSON Configuration (Advanced)**

#### **Add via JSON String**
```bash
# Add complex configuration as JSON
claude mcp add-json --scope=user crawl4ai '{
  "type": "stdio",
  "command": "python",
  "args": ["-m", "mcp_server_crawl4ai"],
  "env": {
    "PATH": "/home/cain/.local/bin:/usr/local/bin:/usr/bin:/bin"
  }
}'
```

### **Method 3: Manual File Editing (Expert Level)**

#### **User Config (`~/.claude.json`)**
```json
{
  "projects": {
    "/path/to/project": {
      "mcpServers": {
        "filesystem": {
          "type": "stdio",
          "command": "npx",
          "args": ["@modelcontextprotocol/server-filesystem", "/home", "/media/cain/linux_storage"],
          "env": {}
        }
      }
    }
  }
}
```

#### **Project Config (`.mcp.json`)**
```json
{
  "mcpServers": {
    "project-db": {
      "type": "stdio",
      "command": "npx",
      "args": ["@company/database-mcp-server"],
      "env": {
        "DB_CONNECTION": "postgresql://..."
      }
    }
  }
}
```

---

## **🛡️ STEP-BY-STEP SAFE INSTALLATION PROCEDURE**

### **PHASE 1: Preparation**
1. **Check Current State**
   ```bash
   claude mcp list  # See what's currently installed
   /mcp             # View active servers in Claude
   ```

2. **Verify Clean Slate**
   ```bash
   # Check configuration files exist and are minimal
   ls -la ~/.claude.json
   ls -la ./.mcp.json
   ls -la ./.claude/settings*.json
   ```

3. **Backup Current Config**
   ```bash
   cp ~/.claude.json ~/.claude.json.backup.$(date +%Y%m%d_%H%M%S)
   ```

### **PHASE 2: Decide Server Scope**

**Decision Matrix:**
- **USER SCOPE** if: You use it in multiple projects, personal tool, no security concerns
- **PROJECT SCOPE** if: Team needs it, project-specific, gets committed to repo
- **LOCAL SCOPE** if: Testing, temporary, or you don't want team to have it

### **PHASE 3: Install Servers One by One**

1. **Start with Essential Servers Only**
   ```bash
   # Example: Just filesystem for file operations
   claude mcp add --scope=user filesystem npx @modelcontextprotocol/server-filesystem /home /media/cain/linux_storage
   ```

2. **Test Each Server**
   ```bash
   # Restart Claude and verify server loads
   claude
   /mcp  # Should show your new server
   # Test a tool from the server
   ```

3. **Add More Servers Gradually**
   ```bash
   # Add one at a time, test each
   claude mcp add --scope=user brave-search npx @modelcontextprotocol/server-brave-search
   ```

### **PHASE 4: Configure Project Settings**

1. **Set Safe Defaults**
   ```bash
   # Create or edit .claude/settings.json
   ```
   ```json
   {
     "enableAllProjectMcpServers": false,
     "enabledMcpjsonServers": [],
     "disabledMcpjsonServers": []
   }
   ```

2. **Explicitly Enable Needed Project Servers**
   ```json
   {
     "enableAllProjectMcpServers": false,
     "enabledMcpjsonServers": ["fk-knowledge", "project-db"],
     "disabledMcpjsonServers": ["untrusted-server"]
   }
   ```

---

## **🚨 CONFLICT AVOIDANCE STRATEGIES**

### **1. Never Use `enableAllProjectMcpServers: true`**
- This setting caused your mass spawning issue
- Always use explicit allow/deny lists instead

### **2. Use Minimal Configurations**
- Start with empty config files
- Add servers one by one
- Test after each addition

### **3. Understand Precedence**
```
Local Project Settings > Project .mcp.json > User ~/.claude.json
```

### **4. Use Scope-Appropriate Locations**
- **Personal tools** → User scope
- **Team tools** → Project scope  
- **Testing/temporary** → Local scope

---

## **📋 MANAGEMENT COMMANDS**

### **List Servers**
```bash
claude mcp list                    # All servers
claude mcp list --scope=user       # User-scoped only
claude mcp list --scope=project    # Project-scoped only
```

### **Remove Servers**
```bash
claude mcp remove --scope=user filesystem
claude mcp remove --scope=project unwanted-server
```

### **Import from Claude Desktop**
```bash
claude mcp add-from-claude-desktop  # Migrate existing config
```

### **Debug Issues**
```bash
claude --mcp-debug                 # Start with MCP debugging
```

---

## **🔧 ENVIRONMENT VARIABLES**

### **Timeout Control**
```bash
export MCP_TIMEOUT=30000           # Server startup timeout (ms)
export MCP_TOOL_TIMEOUT=10000      # Tool execution timeout (ms)
export MAX_MCP_OUTPUT_TOKENS=4096  # Max output size
```

### **Debugging**
```bash
export ANTHROPIC_LOG=debug         # Enable debug logging
export DEBUG=mcp:*                 # MCP-specific debugging
```

---

## **🚨 TROUBLESHOOTING GUIDE**

### **Problem: Too Many Servers Loading**
**Solution:**
1. Check all config files:
   ```bash
   grep -r "mcpServers" ~/.claude.json ./.mcp.json ./.claude/
   ```
2. Disable problematic configs:
   ```bash
   mv ~/.claude.json ~/.claude.json.disabled
   ```
3. Set `enableAllProjectMcpServers: false`

### **Problem: Server Won't Start**
**Debugging Steps:**
1. Test server manually:
   ```bash
   npx @modelcontextprotocol/server-filesystem /home
   ```
2. Check logs:
   ```bash
   claude --mcp-debug
   ```
3. Verify Node.js installation:
   ```bash
   node --version
   npm --version
   ```

### **Problem: Permission Errors**
**Solutions:**
1. Check file permissions
2. Verify paths are absolute
3. Ensure user has access to specified directories

### **Problem: Configuration Corruption**
**Recovery Steps:**
1. Restore from backup:
   ```bash
   cp ~/.claude.json.backup ~/.claude.json
   ```
2. Or reset to minimal config:
   ```bash
   echo '{"mcpServers": {}}' > ~/.claude.json
   ```

---

## **✅ BEST PRACTICES CHECKLIST**

- [ ] Always backup configs before changes
- [ ] Install servers one at a time
- [ ] Test each server after installation
- [ ] Use appropriate scope for each server
- [ ] Never set `enableAllProjectMcpServers: true`
- [ ] Use explicit allow/deny lists
- [ ] Keep configs minimal and clean
- [ ] Document server purposes in team projects
- [ ] Regularly audit installed servers
- [ ] Use version control for project configs

---

## **🎯 RECOMMENDED STARTER CONFIGURATION**

### **User Scope (`~/.claude.json`)**
```json
{
  "projects": {
    "/your/project/path": {
      "mcpServers": {
        "filesystem": {
          "type": "stdio", 
          "command": "npx",
          "args": ["@modelcontextprotocol/server-filesystem", "/home", "/media/cain/linux_storage"],
          "env": {}
        }
      }
    }
  }
}
```

### **Project Settings (`.claude/settings.json`)**
```json
{
  "enableAllProjectMcpServers": false,
  "enabledMcpjsonServers": [],
  "disabledMcpjsonServers": []
}
```

This configuration gives you safe, controlled access to MCP servers without the chaos you experienced before.