# FindersKeepers v2 MCP Session Continuity Server

A powerful MCP (Model Context Protocol) server that provides intelligent session management, conversation logging, and search capabilities for the FindersKeepers v2 project.

## ✅ Complete Setup and Installation

### Prerequisites
- Ubuntu 24.04.2 with NVIDIA RTX 2080 Ti
- Docker containers running (fk2_postgres, fk2_n8n, etc.)
- Python 3.11+
- FindersKeepers v2 infrastructure operational

### Quick Setup

1. **Run the automated setup script:**
```bash
cd /media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-session-server
./setup_fk2_mcp.sh
```

2. **Test the installation:**
```bash
./test_server.sh
```

3. **Add to Claude Desktop configuration:**
Copy the contents of `claude_desktop_config.json` to your Claude Desktop MCP settings.

## 🎯 Features

### Core MCP Tools
- **`start_session`** - Begin new session with full infrastructure integration
- **`end_session`** - End session with data preservation and analytics
- **`resume_session`** - Resume previous session with complete context
- **`log_conversation`** - Log messages to active session
- **`get_session_status`** - View current session statistics
- **`search_sessions`** - Search session history with semantic matching
- **`search_code_snippets`** - Find code across all conversations

### Infrastructure Integration
- **PostgreSQL**: Session and conversation storage
- **n8n Workflows**: Automated data processing
- **Vector Search**: Semantic conversation matching
- **Knowledge Graph**: Relationship mapping
- **GPU Acceleration**: RTX 2080 Ti optimization

## 🔧 Usage Examples

### Starting a Session
```javascript
// MCP call
{
  "method": "tools/call",
  "params": {
    "name": "start_session",
    "arguments": {
      "agent_type": "claude-desktop",
      "project": "finderskeepers-v2",
      "user_id": "fk2_user"
    }
  }
}
```

### Logging Conversations
```javascript
{
  "method": "tools/call",
  "params": {
    "name": "log_conversation",
    "arguments": {
      "message_type": "user_message",
      "content": "How do I implement vector search?",
      "context": {"topic": "technical_question"},
      "tools_used": ["search_sessions"],
      "files_referenced": ["vector_search.py"]
    }
  }
}
```

### Searching Sessions
```javascript
{
  "method": "tools/call",
  "params": {
    "name": "search_sessions",
    "arguments": {
      "query": "docker configuration",
      "limit": 5,
      "include_conversations": true
    }
  }
}
```

### Ending a Session
```javascript
{
  "method": "tools/call",
  "params": {
    "name": "end_session",
    "arguments": {
      "reason": "work_complete",
      "completion_timeout": 30
    }
  }
}
```

## 📊 Database Schema

The server integrates with these PostgreSQL tables:

### agent_sessions
```sql
CREATE TABLE agent_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    agent_type VARCHAR(100),
    user_id VARCHAR(255),
    project VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    context JSONB,
    termination_reason VARCHAR(255)
);
```

### conversation_messages  
```sql
CREATE TABLE conversation_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES agent_sessions(session_id),
    message_type VARCHAR(20) CHECK (message_type IN ('user_message', 'ai_response', 'system_message', 'tool_result')),
    content TEXT NOT NULL,
    context JSONB,
    reasoning TEXT,
    tools_used JSONB,
    files_referenced JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### agent_actions
```sql
CREATE TABLE agent_actions (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES agent_sessions(session_id),
    action_type VARCHAR(100),
    description TEXT,
    details JSONB,
    files_affected JSONB,
    success BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### code_snippets
```sql
CREATE TABLE code_snippets (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES agent_sessions(session_id),
    language VARCHAR(50),
    code TEXT NOT NULL,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);
```

## 🔄 n8n Workflow Integration

The server integrates with two active n8n workflows:

### 1. Session Logger (`/webhook/agent-logger`)
- Processes session start/end events
- Creates/updates agent_sessions table
- Manages session lifecycle
- Notifies FastAPI backend

### 2. Action Tracker (`/webhook/agent-action-tracker`)  
- Logs all conversation messages
- Extracts and stores code snippets
- Tracks file references and tool usage
- Updates conversation_messages table

## 🚀 Manual Server Management

### Start Server
```bash
./start_server.sh
```

### Test Functionality
```bash
./test_server.sh
```

### Environment Configuration
The server uses these environment variables:
- `POSTGRES_URL`: PostgreSQL connection string
- `N8N_WEBHOOK_URL`: n8n base URL for webhooks
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)
- `MCP_MODE`: Protocol mode (stdio for Claude Desktop)

## 🎯 Architecture Benefits

### Session Continuity
- Resume work exactly where you left off
- Full conversation history preservation  
- Context-aware session resumption
- Intelligent next-step suggestions

### Search & Discovery
- Semantic search across all conversations
- Code snippet extraction and indexing
- File reference tracking
- Cross-session relationship mapping

### Infrastructure Integration
- Real-time data processing via n8n
- Vector embeddings for semantic search
- Knowledge graph relationship mapping
- GPU-accelerated processing

### Data Preservation
- Complete conversation logging
- Session analytics and metrics
- Code snippet preservation
- File reference tracking

## 🔍 Troubleshooting

### Database Connection Issues
```bash
# Test PostgreSQL connectivity
python -c "
import asyncio
import asyncpg
asyncio.run(asyncpg.connect('postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2'))
print('✅ Database connected')
"
```

### n8n Webhook Issues
```bash
# Test n8n accessibility
curl -f http://localhost:5678/healthz
```

### MCP Protocol Issues
- Ensure Python virtual environment is activated
- Check that all dependencies are installed
- Verify PostgreSQL tables exist
- Confirm n8n workflows are active

## 📈 Performance Optimization

### GPU Acceleration
- RTX 2080 Ti optimized for ML operations
- Vector processing acceleration
- Parallel embedding generation

### Database Performance
- Optimized PostgreSQL queries
- Proper indexing on session_id columns
- Efficient JSON operations

### Memory Management
- Connection pooling for database
- Streaming processing for large datasets
- Efficient session state management

## 🎉 Success Indicators

✅ **All systems operational:**
- PostgreSQL: Connected with proper schema
- n8n: Workflows active and processing
- MCP Server: Tools registered and responsive
- Claude Desktop: MCP integration working

The FindersKeepers v2 MCP Session Continuity Server provides a complete solution for intelligent conversation management, search, and session continuity in AI-assisted workflows.
