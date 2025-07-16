#!/bin/bash
# 
# FindersKeepers v2 - Complete MCP Session Killer
# Forcefully terminates ALL MCP-related processes and prevents respawning
#

echo "🚨 FindersKeepers v2 - EMERGENCY MCP SESSION KILLER"
echo "=================================================="
echo "⚠️  This will FORCE KILL all MCP-related processes!"
echo

# Function to kill processes by pattern
kill_processes_by_pattern() {
    local pattern="$1"
    local description="$2"
    
    echo "🔍 Looking for $description..."
    PIDS=$(pgrep -f "$pattern" 2>/dev/null)
    
    if [ -n "$PIDS" ]; then
        echo "🎯 Found processes: $PIDS"
        for PID in $PIDS; do
            echo "   💀 Force killing PID $PID..."
            kill -9 "$PID" 2>/dev/null || echo "     ⚠️  Could not kill $PID (may already be dead)"
        done
    else
        echo "   ✅ No $description processes found"
    fi
}

# Kill all MCP Knowledge Server processes
kill_processes_by_pattern "knowledge_server" "MCP Knowledge Server"
kill_processes_by_pattern "mcp-knowledge-server" "MCP Knowledge Server (alt pattern)"

# Kill any Python processes with MCP in the command line
kill_processes_by_pattern "python.*mcp" "Python MCP processes"

# Kill any processes with 'session' and 'mcp' in the command
kill_processes_by_pattern "session.*mcp\|mcp.*session" "MCP session processes"

# Kill specific FastMCP processes
kill_processes_by_pattern "FastMCP" "FastMCP processes"

# Find and kill any remaining zombie processes
echo
echo "🧟 Checking for zombie processes..."
ZOMBIES=$(ps aux | awk '$8 ~ /^Z/ { print $2 }' 2>/dev/null)
if [ -n "$ZOMBIES" ]; then
    echo "🎯 Found zombie processes: $ZOMBIES"
    for PID in $ZOMBIES; do
        echo "   💀 Attempting to clean zombie PID $PID..."
        kill -9 "$PID" 2>/dev/null || echo "     ⚠️  Could not clean zombie $PID"
    done
else
    echo "   ✅ No zombie processes found"
fi

# Clean up PID files and lock files
echo
echo "🧹 Cleaning up PID and lock files..."
rm -f /tmp/mcp_knowledge_server.pid 2>/dev/null && echo "   ✅ Removed MCP PID file" || echo "   ℹ️  No MCP PID file to remove"
rm -f /tmp/mcp_knowledge_server_shutdown 2>/dev/null && echo "   ✅ Removed MCP shutdown flag" || echo "   ℹ️  No shutdown flag to remove"

# Create a temporary flag to prevent immediate respawning
echo
echo "🛡️ Creating anti-respawn flag..."
RESPAWN_FLAG="/tmp/mcp_respawn_disabled_$(date +%s)"
touch "$RESPAWN_FLAG"
echo "   📝 Created flag: $RESPAWN_FLAG"
echo "   ⏰ This flag expires in 5 minutes"

# Schedule flag removal
(sleep 300 && rm -f "$RESPAWN_FLAG" 2>/dev/null && echo "🕰️ Respawn flag expired" || true) &

echo
echo "✅ EMERGENCY CLEANUP COMPLETE!"
echo "💡 All MCP processes have been force-killed"
echo "🛡️ Respawning is temporarily disabled for 5 minutes"
echo "📋 You can now restart services safely"
echo
echo "🚀 To restart MCP Knowledge Server:"
echo "   cd services/mcp-knowledge-server"
echo "   source .venv/bin/activate"
echo "   python src/knowledge_server.py"