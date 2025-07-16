#!/bin/bash

# FindersKeepers v2 - Enhanced MCP Process Group Killer
# Kills entire process groups to prevent zombie processes

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== FindersKeepers v2 Process Group Killer ===${NC}"
echo -e "${YELLOW}This will kill ALL MCP-related process groups${NC}"
echo

# Function to kill process group
kill_process_group() {
    local pid=$1
    local name=$2
    
    # Get process group ID
    local pgid=$(ps -o pgid= -p $pid 2>/dev/null | tr -d ' ')
    
    if [ -n "$pgid" ] && [ "$pgid" != "0" ]; then
        echo -e "${YELLOW}Killing process group $pgid for $name (PID: $pid)${NC}"
        
        # Send SIGTERM to entire process group
        kill -TERM -$pgid 2>/dev/null || true
        sleep 1
        
        # Check if still running
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${RED}Process group still running, sending SIGKILL${NC}"
            kill -KILL -$pgid 2>/dev/null || true
        fi
    else
        # Fallback to individual process kill
        echo -e "${YELLOW}Killing individual process $pid ($name)${NC}"
        kill -TERM $pid 2>/dev/null || true
        sleep 1
        kill -KILL $pid 2>/dev/null || true
    fi
}

# Kill MCP Knowledge Server processes
echo -e "${BLUE}Looking for MCP Knowledge Server processes...${NC}"
for pid in $(pgrep -f "knowledge_server.py" 2>/dev/null); do
    kill_process_group $pid "MCP Knowledge Server"
done

# Kill Python MCP processes
echo -e "${BLUE}Looking for Python MCP processes...${NC}"
for pid in $(pgrep -f "python.*mcp" 2>/dev/null); do
    kill_process_group $pid "Python MCP"
done

# Kill Node.js MCP processes
echo -e "${BLUE}Looking for Node.js MCP processes...${NC}"
for pid in $(pgrep -f "node.*mcp" 2>/dev/null); do
    kill_process_group $pid "Node.js MCP"
done

# Kill npm MCP processes
echo -e "${BLUE}Looking for npm MCP processes...${NC}"
for pid in $(pgrep -f "npm.*mcp" 2>/dev/null); do
    kill_process_group $pid "npm MCP"
done

# Clean up zombie processes
echo -e "${BLUE}Checking for zombie processes...${NC}"
zombies=$(ps aux | grep " <defunct>" | grep -v grep)
if [ -n "$zombies" ]; then
    echo -e "${RED}Found zombie processes:${NC}"
    echo "$zombies"
    echo -e "${YELLOW}Attempting to clean up by killing parent processes...${NC}"
    
    # Get parent PIDs of zombies
    for zpid in $(ps aux | grep " <defunct>" | grep -v grep | awk '{print $2}'); do
        ppid=$(ps -o ppid= -p $zpid 2>/dev/null | tr -d ' ')
        if [ -n "$ppid" ] && [ "$ppid" != "1" ]; then
            echo -e "${YELLOW}Killing parent process $ppid of zombie $zpid${NC}"
            kill -TERM $ppid 2>/dev/null || true
        fi
    done
else
    echo -e "${GREEN}No zombie processes found${NC}"
fi

# Clean up PID files
echo -e "${BLUE}Cleaning up PID files...${NC}"
rm -rf /tmp/fk2-mcp-pids

# Final check
sleep 2
remaining=$(pgrep -f "mcp|knowledge_server" 2>/dev/null | wc -l)
if [ $remaining -eq 0 ]; then
    echo -e "${GREEN}✅ All MCP processes successfully terminated${NC}"
else
    echo -e "${RED}⚠️  Warning: $remaining MCP-related processes may still be running${NC}"
    echo -e "${YELLOW}Run 'ps aux | grep mcp' to check${NC}"
fi

echo -e "${GREEN}Process group cleanup complete!${NC}"