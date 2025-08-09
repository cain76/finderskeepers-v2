#!/bin/bash
# Test script to verify n8n webhook fix for FindersKeepers v2 MCP server
# Run this after fixing the JavaScript syntax error

echo "🧪 Testing FindersKeepers v2 n8n webhook connectivity..."
echo "=================================================="

# Test 1: Basic webhook connectivity
echo "📡 Test 1: Testing agent-logger webhook..."
response1=$(curl -s -X POST http://localhost:5678/webhook/agent-logger \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_fix_verification", 
    "action_type": "session_start",
    "project": "finderskeepers-v2",
    "user_id": "bitcain",
    "agent_type": "claude-code"
  }')

echo "Response: $response1"
echo ""

# Test 2: Test action tracker webhook
echo "📡 Test 2: Testing agent-action-tracker webhook..."
response2=$(curl -s -X POST http://localhost:5678/webhook/agent-action-tracker \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_fix_verification",
    "action_type": "conversation_message", 
    "description": "Test webhook connectivity",
    "success": true
  }')

echo "Response: $response2"
echo ""

# Test 3: Check if responses contain success indicators
echo "🔍 Test 3: Analyzing responses..."

if [[ "$response1" == *"success"* && "$response1" == *"true"* ]]; then
    echo "✅ Agent Logger webhook: WORKING"
else
    echo "❌ Agent Logger webhook: FAILED"
    echo "   Response: $response1"
fi

if [[ "$response2" == *"success"* && "$response2" == *"true"* ]]; then
    echo "✅ Action Tracker webhook: WORKING"
else
    echo "❌ Action Tracker webhook: FAILED"  
    echo "   Response: $response2"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. If webhooks are working, test your MCP server session commands"
echo "2. Try: start_session(), get_session_status(), end_session()"
echo "3. Check n8n execution logs for any remaining issues"
echo ""
echo "📋 n8n Status Check:"
echo "- n8n UI: http://localhost:5678"
echo "- Check 'Executions' tab for recent webhook activity"
echo "- Look for 'FK2-MCP Enhanced Agent Session Logger' workflow executions"
