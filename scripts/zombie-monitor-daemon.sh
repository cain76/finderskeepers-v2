#!/bin/bash

# FindersKeepers v2 - Zombie Process Monitor Daemon
# Continuously monitors and prevents zombie processes

# Log file
LOG_FILE="/var/log/fk2-zombie-monitor.log"
MAX_LOG_SIZE=10485760  # 10MB

# Colors (for terminal output)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to log with timestamp
log() {
    local level=$1
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*" | tee -a "$LOG_FILE"
}

# Function to rotate log file
rotate_log() {
    if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null) -gt $MAX_LOG_SIZE ]; then
        mv "$LOG_FILE" "${LOG_FILE}.old"
        log "INFO" "Log file rotated"
    fi
}

# Function to check and kill zombies
check_zombies() {
    local zombies=$(ps aux | grep " <defunct>" | grep -v grep)
    local zombie_count=$(echo "$zombies" | grep -c "defunct" || echo "0")
    
    if [ $zombie_count -gt 0 ]; then
        log "WARN" "Found $zombie_count zombie processes"
        
        # Try to kill parent processes of zombies
        echo "$zombies" | while read line; do
            local zpid=$(echo "$line" | awk '{print $2}')
            local ppid=$(ps -o ppid= -p $zpid 2>/dev/null | tr -d ' ')
            
            if [ -n "$ppid" ] && [ "$ppid" != "1" ]; then
                local parent_cmd=$(ps -p $ppid -o comm= 2>/dev/null)
                log "INFO" "Zombie PID $zpid has parent PID $ppid ($parent_cmd)"
                
                # Only kill if it's an MCP-related process
                if [[ "$parent_cmd" =~ mcp|knowledge|python|node ]]; then
                    log "WARN" "Killing parent process $ppid to clean zombie $zpid"
                    kill -TERM $ppid 2>/dev/null || true
                fi
            fi
        done
    fi
    
    return $zombie_count
}

# Function to monitor MCP processes
monitor_mcp_processes() {
    local mcp_procs=$(pgrep -f "mcp|knowledge_server" 2>/dev/null | wc -l)
    
    if [ $mcp_procs -gt 0 ]; then
        log "INFO" "Monitoring $mcp_procs MCP-related processes"
        
        # Check for runaway processes (high CPU/memory)
        ps aux | grep -E "mcp|knowledge_server" | grep -v grep | while read line; do
            local pid=$(echo "$line" | awk '{print $2}')
            local cpu=$(echo "$line" | awk '{print $3}')
            local mem=$(echo "$line" | awk '{print $4}')
            local cmd=$(echo "$line" | awk '{print $11}')
            
            # Kill if CPU > 90% or MEM > 50%
            if (( $(echo "$cpu > 90" | bc -l) )) || (( $(echo "$mem > 50" | bc -l) )); then
                log "WARN" "Process $pid ($cmd) using high resources (CPU: $cpu%, MEM: $mem%)"
                log "WARN" "Terminating runaway process $pid"
                kill -TERM $pid 2>/dev/null || true
            fi
        done
    fi
}

# Function to clean orphaned files
clean_orphaned_files() {
    # Clean old PID files
    find /tmp/fk2-mcp-pids -type f -mtime +1 -delete 2>/dev/null || true
    
    # Clean old anti-respawn flags
    find /tmp -name "fk2_mcp_*_anti_respawn" -mtime +1 -delete 2>/dev/null || true
}

# Main monitoring loop
log "INFO" "FindersKeepers v2 Zombie Monitor Daemon started"

# Set up signal handlers
trap 'log "INFO" "Daemon shutting down"; exit 0' SIGTERM SIGINT

# Main loop
while true; do
    rotate_log
    
    # Check for zombies
    check_zombies
    zombie_count=$?
    
    # Monitor MCP processes
    monitor_mcp_processes
    
    # Clean orphaned files every hour
    if [ $(($(date +%s) % 3600)) -lt 60 ]; then
        clean_orphaned_files
    fi
    
    # Status report every 5 minutes
    if [ $(($(date +%s) % 300)) -lt 60 ]; then
        log "INFO" "Status: $zombie_count zombies, $(pgrep -f "mcp|knowledge_server" 2>/dev/null | wc -l) MCP processes"
    fi
    
    # Sleep interval (check every 30 seconds)
    sleep 30
done