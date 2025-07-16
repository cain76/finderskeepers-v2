#!/bin/bash

# Kill Zombie Sessions Script
# This script stops all zombie session processes and cleans up files

echo "🧟‍♂️ Killing zombie sessions and cleaning up files..."

# Kill any running MCP knowledge server processes
echo "1. Killing MCP processes..."
pkill -f "mcp-knowledge-server" || echo "No MCP processes found"
pkill -f "knowledge_server.py" || echo "No knowledge server processes found"
pkill -f "bulletproof_session_logger" || echo "No bulletproof logger processes found"

# Clean up session backup files
echo "2. Cleaning session backup files..."
rm -f /tmp/fk2_session_backup.json /tmp/emergency_session_backup.json
rm -f logs/current_session.json
rm -f .claude/session_backup.json

# Kill any stuck FastAPI processes with infinite loops
echo "3. Checking for stuck FastAPI processes..."
ps aux | grep -E "(uvicorn|fastapi)" | grep -v grep || echo "No FastAPI processes found"

# Clean up any temporary session files
echo "4. Cleaning temporary files..."
find . -name "*session_backup*" -type f -delete 2>/dev/null || echo "No session backup files to clean"
find . -name "current_session*" -type f -delete 2>/dev/null || echo "No current session files to clean"

echo "✅ Zombie session cleanup complete!"
echo "🚫 Session logging is now disabled to prevent recurrence"