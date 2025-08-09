# FindersKeepers v2 - Conversation Capture Fix Documentation

## Problem Identified
Claude Desktop conversations are NOT automatically captured because:
1. **MCP Protocol Limitation**: Conversations don't flow through the MCP protocol
2. **Middleware Can't Access Messages**: The FastMCP middleware only sees tool calls, not conversation content
3. **This is by design**: MCP is for tools, not conversation interception

## Current Status
✅ **What Works:**
- Tool executions ARE captured (vector_search, database_query, etc.)
- Manual conversation capture works perfectly
- FastAPI endpoints process conversations correctly
- Embeddings and knowledge graph are generated when conversations are captured
- Session management works perfectly

❌ **What Doesn't Work:**
- Automatic capture of user messages and Claude responses
- This cannot be fixed without Claude Desktop changes

## Solution: Manual Conversation Capture

### Method 1: Capture Full Exchange
After important conversations, use:
```python
capture_this_conversation(
    user_message="[what the user asked]",
    assistant_response="[what Claude responded]"
)
```

### Method 2: Log Individual Messages
For more control:
```python
log_conversation(
    message_type="user_message",  # or "assistant_response"
    content="[the message content]",
    metadata={"context": "additional info"}
)
```

## How It Works
1. Manual capture sends conversations to FastAPI `/api/mcp/action` endpoint
2. Stored in both `agent_actions` and `conversation_messages` tables
3. Automatically processed for embeddings (Ollama with RTX 2080 Ti)
4. Added to Qdrant vector database
5. Entity extraction creates Neo4j knowledge graph relationships
6. Available for semantic search across sessions

## Database Tables Used
- `agent_sessions`: Session tracking
- `agent_actions`: All actions including conversations
- `conversation_messages`: Dedicated conversation storage
- `documents`: Processed content with embeddings

## No Docker Changes Needed
The system is working correctly. Only the MCP server code was updated to:
1. Add clearer logging messages
2. Include reminders to use manual capture
3. Document the limitation

## Restart Claude Desktop
After the MCP server changes:
1. Close Claude Desktop completely
2. Restart Claude Desktop
3. The new logging messages will appear

## Example Workflow
```python
# 1. Start session
start_session()

# 2. Have conversation with user
# ... conversation happens ...

# 3. Capture important exchanges
capture_this_conversation(
    user_message="search for the conversation data. why are you not logging?",
    assistant_response="I investigated and found that MCP doesn't capture conversations..."
)

# 4. Continue working
vector_search("finderskeepers configuration")

# 5. End session (automatically saves summary)
end_session()
```

## Technical Details
- **MCP Server**: `/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-session-server/src/fk2_mcp_server.py`
- **FastAPI Endpoint**: `/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/api/mcp.py`
- **FastMCP Version**: 2.10.6 (middleware available but limited)

## Future Improvements
Potential solutions (would require significant work):
1. Create a Claude Desktop extension that hooks into conversation events
2. Build a proxy that intercepts Claude Desktop API calls
3. Wait for Anthropic to add conversation capture to MCP protocol
4. Use OS-level text monitoring (privacy concerns)

For now, manual capture is the reliable solution.
