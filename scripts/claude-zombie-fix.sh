#!/bin/bash

# FindersKeepers v2 - Claude CLI Zombie Prevention
# This script monitors and automatically cleans zombies created by Claude CLI

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Lock file to prevent multiple instances
LOCKFILE="/tmp/claude-zombie-fix.lock"
LOGFILE="/tmp/claude-zombie-fix.log"

# Create lock or exit
exec 200>"$LOCKFILE"
if ! flock -n 200; then
    echo "Another instance is already running"
    exit 1
fi

echo -e "${BLUE}=== Claude CLI Zombie Prevention Started ===${NC}"
echo "[$(date)] Started" >> "$LOGFILE"

# Function to clean Claude zombies
clean_claude_zombies() {
    local claude_pids=$(pgrep -x "claude" 2>/dev/null || true)
    
    if [ -z "$claude_pids" ]; then
        return 0
    fi
    
    local zombie_count=0
    
    for claude_pid in $claude_pids; do
        # Count zombies for this Claude process
        local zombies=$(ps --ppid $claude_pid 2>/dev/null | grep "<defunct>" | wc -l || echo 0)
        
        if [ $zombies -gt 0 ]; then
            zombie_count=$((zombie_count + zombies))
            echo -e "${YELLOW}Found $zombies zombies under Claude PID $claude_pid${NC}"
            echo "[$(date)] Found $zombies zombies under Claude PID $claude_pid" >> "$LOGFILE"
            
            # Try to make Claude reap its children
            kill -CHLD $claude_pid 2>/dev/null || true
            sleep 1
            
            # Check if zombies still exist
            local remaining=$(ps --ppid $claude_pid 2>/dev/null | grep "<defunct>" | wc -l || echo 0)
            
            if [ $remaining -gt 0 ]; then
                echo -e "${RED}Failed to clean $remaining zombies from Claude PID $claude_pid${NC}"
                
                # Nuclear option: kill the zombie's direct parents
                ps --ppid $claude_pid 2>/dev/null | grep "<defunct>" | awk '{print $1}' | while read zpid; do
                    # Get the zombie's immediate parent (should be npm/node)
                    local zppid=$(ps -o ppid= -p $zpid 2>/dev/null | tr -d ' ')
                    if [ -n "$zppid" ] && [ "$zppid" != "$claude_pid" ]; then
                        echo -e "${YELLOW}Killing intermediate parent $zppid${NC}"
                        kill -TERM $zppid 2>/dev/null || true
                    fi
                done
            else
                echo -e "${GREEN}Successfully cleaned zombies from Claude PID $claude_pid${NC}"
            fi
        fi
    done
    
    return $zombie_count
}

# Function to prevent new zombies
prevent_new_zombies() {
    # Find all npm/node MCP processes spawned by Claude
    for claude_pid in $(pgrep -x "claude" 2>/dev/null); do
        # Set process group for all children
        ps --ppid $claude_pid -o pid= 2>/dev/null | while read child_pid; do
            # Try to put child in its own process group
            pgid=$(ps -o pgid= -p $child_pid 2>/dev/null | tr -d ' ')
            if [ -n "$pgid" ] && [ "$pgid" = "$claude_pid" ]; then
                # Child is in Claude's process group, fix it
                setpgid $child_pid $child_pid 2>/dev/null || true
            fi
        done
    done
}

# Main monitoring loop
echo -e "${GREEN}Monitoring for Claude zombies...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"

trap 'echo -e "\n${YELLOW}Stopping monitor...${NC}"; exit 0' SIGINT SIGTERM

while true; do
    # Clean existing zombies
    clean_claude_zombies
    zombie_count=$?
    
    # Try to prevent new zombies
    prevent_new_zombies
    
    # Log status every minute
    if [ $(($(date +%s) % 60)) -lt 5 ]; then
        total_zombies=$(ps aux | grep "<defunct>" | grep -v grep | wc -l)
        if [ $total_zombies -gt 0 ]; then
            echo -e "${YELLOW}[$(date +%H:%M:%S)] Total zombies: $total_zombies${NC}"
        fi
    fi
    
    # Sleep for 5 seconds
    sleep 5
done