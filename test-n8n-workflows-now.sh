#!/bin/bash
# test-your-workflows.sh
# Run this to test your imported n8n workflows immediately

echo "🧪 Testing Your Imported FindersKeepers n8n Workflows"
echo "===================================================="

# Webhook URLs (should match what you imported)
SESSION_WEBHOOK="http://localhost:5678/webhook/agent-logger"
ACTION_WEBHOOK="http://localhost:5678/webhook/agent-action-tracker"

echo ""
echo "1. 🔍 Testing n8n Connectivity..."

# Basic connectivity test
if curl -s -I "http://localhost:5678" | head -1 | grep -q "200\|404"; then
    echo "✅ n8n server is responding"
else
    echo "❌ n8n server is not responding"
    echo "Check: docker ps | grep fk2_n8n"
    exit 1
fi

echo ""
echo "2. 🧪 Testing Session Creation Webhook..."

# Test session creation
echo "📤 Sending session creation request..."
session_response=$(curl -s -w "%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "agent_type": "test_agent",
        "user_id": "bitcain",
        "project": "finderskeepers-v2-test",
        "action_type": "session_start"
    }' \
    "$SESSION_WEBHOOK")

# Extract HTTP status code (last 3 characters)
http_status="${session_response: -3}"
response_body="${session_response%???}"

echo "HTTP Status: $http_status"
echo "Response: $response_body"

if [ "$http_status" = "200" ]; then
    echo "✅ Session webhook is responding"
    
    # Try to extract session_id
    if echo "$response_body" | grep -q "session_id"; then
        SESSION_ID=$(echo "$response_body" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
        echo "✅ Session created successfully: $SESSION_ID"
    else
        echo "⚠️  Webhook responded but no session_id found"
        echo "Response: $response_body"
        SESSION_ID="test_session_$(date +%s)"
        echo "Using fallback session_id: $SESSION_ID"
    fi
else
    echo "❌ Session webhook failed with status: $http_status"
    echo "Response: $response_body"
    
    # Check if it's a workflow issue
    if [ "$http_status" = "404" ]; then
        echo ""
        echo "🔍 Webhook not found - possible issues:"
        echo "  1. Workflow not imported correctly"
        echo "  2. Webhook path mismatch (should be: /webhook/agent-logger)"
        echo "  3. Workflow not activated"
        echo ""
        echo "Check in n8n UI: http://localhost:5678"
    fi
    exit 1
fi

echo ""
echo "3. 🧪 Testing Action Tracker Webhook..."

# Test regular action logging
echo "📤 Sending regular action request..."
action_response=$(curl -s -w "%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "{
        \"session_id\": \"$SESSION_ID\",
        \"action_type\": \"tool_call\",
        \"description\": \"User called search_documents tool\",
        \"files_affected\": [],
        \"details\": {
            \"tool\": \"search_documents\",
            \"query\": \"test query\"
        },
        \"success\": true
    }" \
    "$ACTION_WEBHOOK")

action_http_status="${action_response: -3}"
action_response_body="${action_response%???}"

echo "HTTP Status: $action_http_status"
echo "Response: $action_response_body"

if [ "$action_http_status" = "200" ]; then
    echo "✅ Action webhook is responding"
else
    echo "❌ Action webhook failed with status: $action_http_status"
fi

echo ""
echo "4. 🧪 Testing Conversation Message Logging..."

# Test conversation message
echo "📤 Sending conversation message..."
conv_response=$(curl -s -w "%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "{
        \"session_id\": \"$SESSION_ID\",
        \"action_type\": \"conversation_message\",
        \"description\": \"User message captured\",
        \"files_affected\": [],
        \"details\": {
            \"message_type\": \"user_message\",
            \"content\": \"Hello, how does the session continuity system work?\",
            \"context\": {
                \"emotional_tone\": \"curious\",
                \"topic\": \"system_architecture\"
            },
            \"reasoning\": \"User asking about system functionality\",
            \"tools_used\": [],
            \"files_referenced\": []
        },
        \"success\": true
    }" \
    "$ACTION_WEBHOOK")

conv_http_status="${conv_response: -3}"
conv_response_body="${conv_response%???}"

echo "HTTP Status: $conv_http_status"  
echo "Response: $conv_response_body"

if [ "$conv_http_status" = "200" ]; then
    echo "✅ Conversation webhook is responding"
else
    echo "❌ Conversation webhook failed with status: $conv_http_status"
fi

echo ""
echo "5. 🔍 Checking PostgreSQL Database..."

# Check if data was actually stored
if docker exec fk2_postgres psql -U postgres -d finderskeepers -c "\dt" > /dev/null 2>&1; then
    echo "✅ PostgreSQL is accessible"
    
    echo ""
    echo "Checking for session record..."
    session_count=$(docker exec fk2_postgres psql -U postgres -d finderskeepers -t -c \
        "SELECT COUNT(*) FROM agent_sessions WHERE session_id = '$SESSION_ID';" 2>/dev/null | tr -d ' ')
    
    if [ "$session_count" -gt 0 ]; then
        echo "✅ Session found in database"
        docker exec fk2_postgres psql -U postgres -d finderskeepers -c \
            "SELECT session_id, agent_type, user_id, status, start_time FROM agent_sessions WHERE session_id = '$SESSION_ID';"
    else
        echo "❌ Session not found in database"
        echo "This indicates a workflow or database connection issue"
    fi
    
    echo ""
    echo "Checking for action records..."
    action_count=$(docker exec fk2_postgres psql -U postgres -d finderskeepers -t -c \
        "SELECT COUNT(*) FROM agent_actions WHERE session_id = '$SESSION_ID';" 2>/dev/null | tr -d ' ')
    
    if [ "$action_count" -gt 0 ]; then
        echo "✅ Actions found in database ($action_count records)"
        docker exec fk2_postgres psql -U postgres -d finderskeepers -c \
            "SELECT action_type, description, success, created_at FROM agent_actions WHERE session_id = '$SESSION_ID' ORDER BY created_at;"
    else
        echo "❌ No actions found in database"
    fi
    
    echo ""
    echo "Checking for conversation messages..."
    conv_count=$(docker exec fk2_postgres psql -U postgres -d finderskeepers -t -c \
        "SELECT COUNT(*) FROM conversation_messages WHERE session_id = '$SESSION_ID';" 2>/dev/null | tr -d ' ')
    
    if [ "$conv_count" -gt 0 ]; then
        echo "✅ Conversation messages found in database ($conv_count records)"
        docker exec fk2_postgres psql -U postgres -d finderskeepers -c \
            "SELECT message_type, content, created_at FROM conversation_messages WHERE session_id = '$SESSION_ID' ORDER BY created_at;"
    else
        echo "❌ No conversation messages found in database"
    fi
    
else
    echo "❌ Cannot access PostgreSQL database"
    echo "Check: docker ps | grep fk2_postgres"
fi

echo ""
echo "📊 SUMMARY"
echo "=========="
echo "Session Creation: $([ "$http_status" = "200" ] && echo "✅ Working" || echo "❌ Failed")"
echo "Action Logging: $([ "$action_http_status" = "200" ] && echo "✅ Working" || echo "❌ Failed")"  
echo "Conversation Logging: $([ "$conv_http_status" = "200" ] && echo "✅ Working" || echo "❌ Failed")"
echo "Database Storage: $([ "${session_count:-0}" -gt 0 ] && echo "✅ Working" || echo "❌ Failed")"

echo ""
if [ "$http_status" = "200" ] && [ "$action_http_status" = "200" ] && [ "$conv_http_status" = "200" ] && [ "${session_count:-0}" -gt 0 ]; then
    echo "🎉 SUCCESS: Your n8n workflows are working perfectly!"
    echo ""
    echo "✅ Ready for MCP server integration"
    echo "✅ Session management working"
    echo "✅ Action logging working"
    echo "✅ Conversation capture working"  
    echo "✅ Database persistence working"
    echo ""
    echo "Next step: Update your MCP Knowledge Server to use these webhooks"
else
    echo "❌ ISSUES FOUND: Some workflows are not working properly"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check n8n workflow logs in UI: http://localhost:5678"
    echo "2. Verify PostgreSQL credentials in n8n"
    echo "3. Check container logs: docker logs fk2_n8n"
fi

echo ""
echo "Test session_id for reference: $SESSION_ID"