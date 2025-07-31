#!/bin/bash

# FindersKeepers v2 - Pipeline Validation Script for bitcain
# This script tests that conversation logging is working properly

echo "🧪 FindersKeepers v2 - Conversation Logging Pipeline Test"
echo "=========================================================="

echo "📡 Testing n8n webhook endpoints..."

#!/bin/bash

# FindersKeepers v2 - COMPREHENSIVE Pipeline Validation Script for bitcain
# This script tests all conversation data types and processing capabilities

echo "🧪 FindersKeepers v2 - COMPREHENSIVE Conversation Logging Pipeline Test"
echo "================================================================================"

echo "📡 Testing n8n webhook endpoints with FULL conversation data types..."

# Test session-logger webhook (CORRECT ENDPOINT)
echo "1. Testing session-logger webhook..."
curl -X POST http://localhost:5678/webhook/session-logger \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_comprehensive_validation", 
    "action_type": "session_start",
    "user_id": "bitcain",
    "agent_type": "claude-desktop",
    "project": "finderskeepers-v2",
    "context": {
      "gpu_model": "RTX_2080Ti",
      "os": "Ubuntu_24.04.2",
      "docker_user": "bitcainnet",
      "project_repo": "https://github.com/cain76/finderskeepers-v2"
    },
    "timestamp": "'$(date -Iseconds)'",
    "source": "comprehensive_validation_script"
  }' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s

echo ""

# Test 2: User message with complex question about project
echo "2. Testing user message with project context..."
curl -X POST http://localhost:5678/webhook/action-tracker \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_comprehensive_validation",
    "action_type": "conversation_message",
    "description": "user_message: Complex question about FindersKeepers v2 configuration",
    "details": {
      "message_type": "user_message",
      "content": "Claude, I need help fixing the fk2-mcp server webhook endpoints. Looking at /media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-session-server/src/fk2_mcp_server.py - can you check if the webhooks match the active n8n workflows? Also check our repo at https://github.com/cain76/finderskeepers-v2 for any updates.",
      "context": {
        "user": "bitcain",
        "project": "finderskeepers-v2",
        "files_referenced": ["/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-session-server/src/fk2_mcp_server.py"],
        "urls_mentioned": ["https://github.com/cain76/finderskeepers-v2"],
        "tools_requested": ["file_analysis", "webhook_validation"]
      },
      "reasoning": "User needs webhook configuration validation",
      "tools_used": [],
      "files_referenced": ["/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-session-server/src/fk2_mcp_server.py"]
    },
    "success": true,
    "timestamp": "'$(date -Iseconds)'",
    "source": "comprehensive_validation_script"
  }' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s

echo ""

# Test 3: Assistant response with code snippets
echo "3. Testing assistant response with embedded code snippets..."
curl -X POST http://localhost:5678/webhook/action-tracker \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_comprehensive_validation",
    "action_type": "conversation_message",
    "description": "assistant_response: Code analysis and webhook configuration fix",
    "details": {
      "message_type": "assistant_response",
      "content": "I found the issue! The webhook endpoints in your fk2-mcp server don'\''t match the active n8n workflows. Here'\''s the fix:\n\n```python\n# CORRECTED: Use the ACTUAL n8n webhook endpoints\nN8N_BASE_URL = os.getenv(\"N8N_WEBHOOK_URL\", \"http://localhost:5678\")\n\n# FIXED: Use correct webhook endpoints from active n8n workflows\nSESSION_WEBHOOK = f\"{N8N_BASE_URL}/webhook/session-logger\"       # FK2-MCP Enhanced Agent Session Logger\nACTION_WEBHOOK = f\"{N8N_BASE_URL}/webhook/action-tracker\"        # FK2-MCP Agent Action Tracker\n\n# CONVERSATION LOGGING: action-tracker webhook processes conversation_message actions  \nCONVERSATION_WEBHOOK = f\"{N8N_BASE_URL}/webhook/action-tracker\"  # Same as ACTION_WEBHOOK\n```\n\nAlso, you need to update your docker-compose.yml networking:\n\n```yaml\nservices:\n  n8n:\n    container_name: fk2_n8n\n    ports:\n      - \"5678:5678\"\n    networks:\n      shared-network:\n        aliases:\n          - n8n\n```\n\nAnd here'\''s a bash script to test the endpoints:\n\n```bash\n#!/bin/bash\necho \"Testing FindersKeepers v2 webhooks...\"\ncurl -X POST http://localhost:5678/webhook/action-tracker \\\n  -H \"Content-Type: application/json\" \\\n  -d '\''{\"session_id\": \"test\", \"action_type\": \"conversation_message\"}'\''\n```\n\nThe repository at https://github.com/cain76/finderskeepers-v2 should be updated with these fixes.",
      "context": {
        "user": "bitcain",
        "project": "finderskeepers-v2",
        "code_analysis_performed": true,
        "files_analyzed": ["/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-session-server/src/fk2_mcp_server.py"],
        "languages_used": ["python", "yaml", "bash"],
        "repository_referenced": "https://github.com/cain76/finderskeepers-v2"
      },
      "reasoning": "Analyzed webhook configuration and provided comprehensive fix with code examples",
      "tools_used": ["code_analysis", "file_inspection", "webhook_validation"],
      "files_referenced": [
        "/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-session-server/src/fk2_mcp_server.py",
        "/media/cain/linux_storage/projects/finderskeepers-v2/docker-compose.yml"
      ]
    },
    "success": true,
    "timestamp": "'$(date -Iseconds)'",
    "source": "comprehensive_validation_script"
  }' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s

echo ""

# Test 4: Tool execution with results
echo "4. Testing tool execution logging..."
curl -X POST http://localhost:5678/webhook/action-tracker \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_comprehensive_validation",
    "action_type": "conversation_message",
    "description": "tool_execution: desktop-commander file edit operation",
    "details": {
      "message_type": "tool_execution",
      "content": "Successfully executed desktop-commander:edit_block on /media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-session-server/src/fk2_mcp_server.py - Fixed webhook endpoint configuration. Changed ACTION_WEBHOOK from agent-logger to action-tracker to match active n8n workflow.",
      "context": {
        "user": "bitcain",
        "project": "finderskeepers-v2",
        "tool_name": "desktop-commander",
        "tool_operation": "edit_block",
        "file_modified": "/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-session-server/src/fk2_mcp_server.py",
        "lines_changed": 3,
        "backup_created": false
      },
      "reasoning": "Fixed critical webhook endpoint mismatch that was preventing conversation logging",
      "tools_used": ["desktop-commander"],
      "files_referenced": ["/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-session-server/src/fk2_mcp_server.py"]
    },
    "success": true,
    "timestamp": "'$(date -Iseconds)'",
    "source": "comprehensive_validation_script"
  }' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s

echo ""

# Test 5: Error handling and recovery
echo "5. Testing error handling and recovery logging..."
curl -X POST http://localhost:5678/webhook/action-tracker \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_comprehensive_validation",
    "action_type": "conversation_message",
    "description": "system_error: Webhook endpoint mismatch detected and resolved",
    "details": {
      "message_type": "system_error",
      "content": "ERROR: Connection failed to http://localhost:5678/webhook/agent-logger - endpoint does not exist. RESOLUTION: Updated configuration to use correct endpoint /webhook/action-tracker which matches active n8n workflow FK2-MCP Agent Action Tracker.",
      "context": {
        "user": "bitcain",
        "project": "finderskeepers-v2",
        "error_type": "webhook_endpoint_mismatch",
        "original_endpoint": "/webhook/agent-logger",
        "corrected_endpoint": "/webhook/action-tracker",
        "validation_method": "n8n_workflow_inspection",
        "recovery_action": "configuration_update"
      },
      "reasoning": "System detected and automatically corrected webhook endpoint configuration error",
      "tools_used": ["n8n-mcp", "configuration_validation"],
      "files_referenced": ["/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-session-server/src/fk2_mcp_server.py"]
    },
    "success": true,
    "timestamp": "'$(date -Iseconds)'",
    "source": "comprehensive_validation_script"
  }' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s

echo ""

# Test database connectivity
echo "6. Testing PostgreSQL database..."
docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -c "
SELECT 
    COUNT(*) as total_documents,
    COUNT(CASE WHEN created_at > NOW() - INTERVAL '1 hour' THEN 1 END) as recent_documents
FROM documents;" 2>/dev/null || echo "❌ Database connection failed"

echo ""

echo "7. Testing conversation message storage..."
docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -c "
SELECT 
    COUNT(*) as total_conversations,
    COUNT(CASE WHEN created_at > NOW() - INTERVAL '5 minutes' THEN 1 END) as recent_test_messages,
    COUNT(CASE WHEN content LIKE '%comprehensive_validation%' THEN 1 END) as validation_messages
FROM conversation_messages;" 2>/dev/null || echo "❌ Conversation table query failed"

echo ""

echo "8. Testing code snippet extraction..."
docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -c "
SELECT 
    COUNT(*) as total_code_snippets,
    COUNT(CASE WHEN extracted_at > NOW() - INTERVAL '5 minutes' THEN 1 END) as recent_extractions,
    array_agg(DISTINCT language) as languages_detected
FROM code_snippets;" 2>/dev/null || echo "❌ Code snippets table query failed"

echo ""

# Test other services
echo "9. Testing other service endpoints..."
echo "FastAPI Health: $(curl -s http://localhost:8000/health 2>/dev/null | head -c 100)..."
echo "Qdrant Collections: $(curl -s http://localhost:6333/collections 2>/dev/null | head -c 100)..."
echo "n8n Health: $(curl -s http://localhost:5678/healthz 2>/dev/null | head -c 50)..."

echo ""
echo "🎯 COMPREHENSIVE PIPELINE VALIDATION COMPLETE"
echo ""
echo "✅ EXPECTED RESULTS:"
echo "- HTTP 200 responses for all webhook tests"
echo "- Database shows recent conversation messages from this test"
echo "- Code snippets extracted and stored (Python, YAML, Bash)"
echo "- File references tracked: fk2_mcp_server.py, docker-compose.yml"
echo "- URLs processed: https://github.com/cain76/finderskeepers-v2"
echo "- Tool usage logged: desktop-commander, n8n-mcp"
echo ""
echo "❌ TROUBLESHOOTING:"
echo "If HTTP 404/500 responses:"
echo "  docker logs fk2_n8n --tail 20"
echo "  docker ps | grep fk2_"
echo ""
echo "If database issues:"
echo "  docker logs fk2_postgres --tail 10"
echo "  docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -c '\dt'"
echo ""
echo "🚀 Ready for COMPREHENSIVE AI GOD STATUS validation!"
echo "   Use fk2-mcp server tools:"
echo "   - start_session()"
echo "   - test_webhooks()"
echo "   - capture_this_conversation() with complex data"
echo ""
echo "🧠⚡ FINDERSKEEPERS V2 FULL PIPELINE TEST COMPLETE!"

echo ""

# Test database connectivity
echo "3. Testing PostgreSQL database..."
docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -c "SELECT COUNT(*) as document_count FROM documents;" 2>/dev/null || echo "❌ Database connection failed"

echo ""

# Test other services
echo "4. Testing other services..."
echo "FastAPI: $(curl -s http://localhost:8000/health | head -c 50)..."
echo "Qdrant: $(curl -s http://localhost:6333/collections | head -c 50)..."

echo ""
echo "🎯 PIPELINE VALIDATION COMPLETE"
echo ""
echo "✅ If HTTP 200 responses above, the pipeline is working!"
echo "❌ If HTTP 404/500 responses, check n8n workflows are active"
echo ""
echo "🔍 Check n8n logs if issues:"
echo "docker logs fk2_n8n --tail 20"
echo ""
echo "🚀 Ready for AI GOD STATUS testing!"
