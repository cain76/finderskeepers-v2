#!/bin/bash

# FindersKeepers v2 - Zombie Prevention Wrapper
# This script wraps MCP processes to ensure proper cleanup and prevent zombie processes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# PID file for tracking
PID_DIR="/tmp/fk2-mcp-pids"
mkdir -p "$PID_DIR"

# Function to cleanup on exit
cleanup() {
    local exit_code=$?
    echo -e "${YELLOW}[$(date)] Cleaning up process group...${NC}"
    
    # Kill entire process group
    if [ -n "$PGID" ]; then
        # Send SIGTERM to process group
        kill -TERM -$PGID 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        kill -KILL -$PGID 2>/dev/null || true
    fi
    
    # Clean up PID file
    if [ -n "$PID_FILE" ]; then
        rm -f "$PID_FILE"
    fi
    
    # Wait for all child processes
    wait
    
    echo -e "${GREEN}[$(date)] Cleanup complete${NC}"
    exit $exit_code
}

# Set up signal handlers
trap cleanup EXIT SIGINT SIGTERM SIGHUP

# Function to monitor and reap child processes
reap_zombies() {
    while true; do
        # Wait for any child process to exit
        wait -n 2>/dev/null || true
        
        # Check for zombies and log
        local zombies=$(ps aux | grep " <defunct>" | grep -v grep | wc -l)
        if [ $zombies -gt 0 ]; then
            echo -e "${RED}[$(date)] Found $zombies zombie processes, attempting cleanup...${NC}"
            # Force wait on all children
            wait
        fi
        
        sleep 5
    done
}

# Parse arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <command> [args...]"
    echo "Example: $0 python src/knowledge_server.py"
    exit 1
fi

COMMAND="$@"
SERVICE_NAME=$(echo "$1" | sed 's/[^a-zA-Z0-9]/_/g')
PID_FILE="$PID_DIR/${SERVICE_NAME}_$(date +%s).pid"

echo -e "${GREEN}=== FindersKeepers v2 Zombie Prevention Wrapper ===${NC}"
echo -e "${YELLOW}Starting: $COMMAND${NC}"
echo -e "${YELLOW}PID file: $PID_FILE${NC}"

# Start zombie reaper in background
reap_zombies &
REAPER_PID=$!

# Create new process group and run command
set -m  # Enable job control
$COMMAND &
MAIN_PID=$!
PGID=$(ps -o pgid= -p $MAIN_PID | tr -d ' ')

# Save PID info
echo "$MAIN_PID:$PGID" > "$PID_FILE"

echo -e "${GREEN}Started with PID: $MAIN_PID, PGID: $PGID${NC}"

# Wait for main process
wait $MAIN_PID
MAIN_EXIT_CODE=$?

# Kill the reaper
kill $REAPER_PID 2>/dev/null || true

echo -e "${YELLOW}Process exited with code: $MAIN_EXIT_CODE${NC}"

# Trigger cleanup
exit $MAIN_EXIT_CODE