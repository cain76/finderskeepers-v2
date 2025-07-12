#!/bin/bash
# 
# FindersKeepers v2 - MCP Session Cleanup Script
# Gracefully terminates stuck MCP Knowledge Server sessions
#

echo "🧹 FindersKeepers v2 - MCP Session Cleanup"
echo "=========================================="

# Find and kill mcp-knowledge-server processes
MCP_PROCESSES=$(ps aux | grep "mcp-knowledge-server\|knowledge_server.py" | grep -v grep | awk '{print $2}')

if [ -z "$MCP_PROCESSES" ]; then
    echo "✅ No stuck MCP Knowledge Server processes found"
else
    echo "🔍 Found MCP processes to terminate:"
    ps aux | grep "mcp-knowledge-server\|knowledge_server.py" | grep -v grep
    echo
    
    for PID in $MCP_PROCESSES; do
        echo "🛑 Terminating process $PID gracefully..."
        kill -TERM $PID
        sleep 2
        
        # Check if process is still running
        if kill -0 $PID 2>/dev/null; then
            echo "⚠️  Process $PID still running, forcing termination..."
            kill -KILL $PID
        fi
    done
fi

# Find any other Python processes that might be related to session logging
echo
echo "🔍 Checking for related Python processes..."
RELATED_PROCESSES=$(ps aux | grep python | grep -E "(session|activity_logger|mcp)" | grep -v grep | awk '{print $2}')

if [ -n "$RELATED_PROCESSES" ]; then
    echo "⚠️  Found potentially related processes:"
    ps aux | grep python | grep -E "(session|activity_logger|mcp)" | grep -v grep
    echo
    echo "ℹ️  These processes may be related to session logging."
    echo "   Review manually if needed: kill -TERM <pid>"
fi

echo
echo "✅ MCP session cleanup complete!"
echo "💡 Tip: Sessions should now properly terminate when you use Ctrl+C or when the process exits"