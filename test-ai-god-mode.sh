#!/bin/bash

# AI GOD MODE Test Script - Validate persistent memory system
# This script tests the complete AI GOD MODE workflow

echo "🧠 AI GOD MODE SYSTEM TEST"
echo "=========================="

# Test 1: Check if AI GOD MODE schema exists
echo "🔍 Test 1: Checking AI GOD MODE schema..."
SCHEMA_EXISTS=$(docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ai_session_memory');" | tr -d ' ')

if [ "$SCHEMA_EXISTS" = "t" ]; then
    echo "✅ AI GOD MODE schema exists"
else
    echo "❌ AI GOD MODE schema missing - run setup-ai-god-mode.sh first"
    exit 1
fi

# Test 2: Check FastAPI endpoints
echo "🔍 Test 2: Testing FastAPI endpoints..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/mcp/health")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ AI GOD MODE endpoints responding"
else
    echo "❌ AI GOD MODE endpoints not responding (HTTP $HTTP_CODE)"
    echo "   Check if containers are running: docker ps"
    exit 1
fi

# Test 3: Test session lifecycle with API
echo "🔍 Test 3: Testing session lifecycle..."

# Generate test session ID
TEST_SESSION="test_ai_god_mode_$(date +%s)"

# Start session
echo "  📝 Starting test session..."
START_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/mcp/session/start" \
    -H "Content-Type: application/json" \
    -d "{
        \"session_id\": \"$TEST_SESSION\",
        \"agent_type\": \"claude-desktop-ai-god-mode\",
        \"user_id\": \"bitcain\",
        \"project\": \"test-ai-god-mode\",
        \"timestamp\": \"$(date -Iseconds)\",
        \"source\": \"ai_god_mode_test\",
        \"ai_god_mode\": true
    }")

if echo "$START_RESPONSE" | grep -q "\"status\".*\"ok\""; then
    echo "  ✅ Session start successful"
else
    echo "  ❌ Session start failed: $START_RESPONSE"
    exit 1
fi

# Log some test actions
echo "  📝 Logging test actions..."
for i in {1..3}; do
    ACTION_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/mcp/action" \
        -H "Content-Type: application/json" \
        -d "{
            \"session_id\": \"$TEST_SESSION\",
            \"action_type\": \"conversation_message\",
            \"description\": \"Test conversation message $i\",
            \"details\": {
                \"message_type\": \"test_message\",
                \"content\": \"This is AI GOD MODE test message number $i for session $TEST_SESSION\",
                \"context\": {
                    \"test\": true,
                    \"message_number\": $i
                }
            },
            \"success\": true,
            \"timestamp\": \"$(date -Iseconds)\",
            \"source\": \"ai_god_mode_test\",
            \"ai_god_mode\": true
        }")
    
    if echo "$ACTION_RESPONSE" | grep -q "\"status\".*\"ok\""; then
        echo "    ✅ Test action $i logged"
    else
        echo "    ❌ Test action $i failed"
    fi
done

# End session with summary
echo "  📝 Ending test session..."
SUMMARY="AI GOD MODE test session completed successfully with 3 test messages. All functionality working correctly."

END_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/mcp/session/end" \
    -H "Content-Type: application/json" \
    -d "{
        \"session_id\": \"$TEST_SESSION\",
        \"reason\": \"ai_god_mode_test_complete\",
        \"summary\": \"$SUMMARY\",
        \"timestamp\": \"$(date -Iseconds)\",
        \"user_id\": \"bitcain\",
        \"agent_type\": \"claude-desktop-ai-god-mode\",
        \"project\": \"test-ai-god-mode\",
        \"ai_god_mode\": true,
        \"accomplishments_count\": 3,
        \"conversations_count\": 3
    }")

if echo "$END_RESPONSE" | grep -q "\"status\".*\"ok\""; then
    echo "  ✅ Session end successful"
else
    echo "  ❌ Session end failed: $END_RESPONSE"
    exit 1
fi

# Test 4: Verify data persistence
echo "🔍 Test 4: Verifying data persistence..."
sleep 2  # Give database time to commit

# Check if session is in AI GOD MODE table
SESSION_COUNT=$(docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -t -c "SELECT COUNT(*) FROM ai_session_memory WHERE session_id = '$TEST_SESSION';" | tr -d ' ')

if [ "$SESSION_COUNT" = "1" ]; then
    echo "✅ Session persisted in AI GOD MODE table"
else
    echo "❌ Session not found in AI GOD MODE table"
    exit 1
fi

# Check if actions were logged
ACTION_COUNT=$(docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -t -c "SELECT COUNT(*) FROM agent_actions WHERE session_id = '$TEST_SESSION';" | tr -d ' ')

if [ "$ACTION_COUNT" -ge "3" ]; then
    echo "✅ Actions persisted ($ACTION_COUNT actions found)"
else
    echo "❌ Actions not properly persisted ($ACTION_COUNT actions found)"
    exit 1
fi

# Test 5: Test resume context endpoint
echo "🔍 Test 5: Testing resume context..."
CONTEXT_RESPONSE=$(curl -s "http://localhost:8000/api/mcp/ai-god-mode/resume-context/bitcain?project=test-ai-god-mode")

if echo "$CONTEXT_RESPONSE" | grep -q "\"status\".*\"context_available\""; then
    echo "✅ Resume context available"
else
    echo "❌ Resume context not available: $CONTEXT_RESPONSE"
    exit 1
fi

# Test 6: Test search functionality
echo "🔍 Test 6: Testing search functionality..."
SEARCH_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/mcp/ai-god-mode/search" \
    -H "Content-Type: application/json" \
    -d "{
        \"query\": \"test message\",
        \"user_id\": \"bitcain\",
        \"limit\": 5
    }")

if echo "$SEARCH_RESPONSE" | grep -q "$TEST_SESSION"; then
    echo "✅ Search functionality working"
else
    echo "❌ Search functionality failed"
    exit 1
fi

# Cleanup test data
echo "🧹 Cleaning up test data..."
docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -c "DELETE FROM ai_session_memory WHERE session_id = '$TEST_SESSION';" > /dev/null
docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -c "DELETE FROM agent_actions WHERE session_id = '$TEST_SESSION';" > /dev/null
docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -c "DELETE FROM agent_sessions WHERE session_id = '$TEST_SESSION';" > /dev/null
docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -c "DELETE FROM conversation_messages WHERE session_id = '$TEST_SESSION';" > /dev/null

echo "✅ Test data cleaned up"

echo ""
echo "🎉 AI GOD MODE SYSTEM TEST PASSED!"
echo ""
echo "🧠 ALL TESTS SUCCESSFUL:"
echo "✅ Database schema exists"
echo "✅ FastAPI endpoints responding"
echo "✅ Session lifecycle working"
echo "✅ Data persistence confirmed"
echo "✅ Resume context available"
echo "✅ Search functionality operational"
echo ""
echo "🚀 AI GOD MODE IS FULLY OPERATIONAL!"
echo "🧠 Persistent memory system ready for use"
echo ""
echo "📱 USAGE:"
echo "1. Start MCP server: services/mcp-session-server/src/fk2_mcp_server.py"
echo "2. Use start_session() to begin AI GOD MODE"
echo "3. Use end_session() to save comprehensive summaries"
echo "4. Use resume_session() to restore perfect context"
echo ""
echo "🔗 Monitor at: http://localhost:8000/api/mcp/health"
