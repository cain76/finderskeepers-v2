#!/bin/bash
# 
# Monitor Zombie Processes Script
# Shows zombie processes that keep regenerating and helps identify patterns
#

echo "🔍 Zombie Process Monitor for FindersKeepers v2"
echo "==============================================="
echo "This script will continuously monitor for zombie processes and show regeneration patterns"
echo "Press Ctrl+C to stop monitoring"
echo ""

# Function to get current timestamp
get_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

# Function to check for zombie processes
check_zombies() {
    local timestamp=$(get_timestamp)
    local zombies=$(ps aux | awk '$8 ~ /^Z/ { print $2 " " $11 }' 2>/dev/null)
    
    if [ -n "$zombies" ]; then
        echo "[$timestamp] 🧟 ZOMBIE PROCESSES DETECTED:"
        echo "$zombies" | while read pid cmd; do
            echo "  ├─ PID: $pid, Command: $cmd"
        done
        echo ""
        return 0
    else
        echo "[$timestamp] ✅ No zombie processes found"
        return 1
    fi
}

# Function to check for MCP-related processes
check_mcp_processes() {
    local timestamp=$(get_timestamp)
    echo "[$timestamp] 🔍 MCP-related processes:"
    
    # Check for knowledge server processes
    local knowledge_procs=$(pgrep -f "knowledge_server" 2>/dev/null)
    if [ -n "$knowledge_procs" ]; then
        echo "  ├─ Knowledge Server PIDs: $knowledge_procs"
    fi
    
    # Check for MCP processes
    local mcp_procs=$(pgrep -f "mcp" 2>/dev/null)
    if [ -n "$mcp_procs" ]; then
        echo "  ├─ MCP-related PIDs: $mcp_procs"
    fi
    
    # Check for bulletproof logger
    local bullet_procs=$(pgrep -f "bulletproof" 2>/dev/null)
    if [ -n "$bullet_procs" ]; then
        echo "  ├─ Bulletproof Logger PIDs: $bullet_procs"
    fi
    
    # Check for session-related processes
    local session_procs=$(pgrep -f "session.*log\|log.*session" 2>/dev/null)
    if [ -n "$session_procs" ]; then
        echo "  ├─ Session Logger PIDs: $session_procs"
    fi
    
    if [ -z "$knowledge_procs" ] && [ -z "$mcp_procs" ] && [ -z "$bullet_procs" ] && [ -z "$session_procs" ]; then
        echo "  └─ No MCP-related processes found"
    fi
    echo ""
}

# Function to check for rapid process spawning
monitor_process_spawning() {
    local timestamp=$(get_timestamp)
    local current_proc_count=$(ps aux | wc -l)
    
    if [ -n "$last_proc_count" ]; then
        local proc_diff=$((current_proc_count - last_proc_count))
        if [ $proc_diff -gt 5 ]; then
            echo "[$timestamp] ⚠️  RAPID PROCESS SPAWNING DETECTED: +$proc_diff processes in 5 seconds!"
        elif [ $proc_diff -gt 0 ]; then
            echo "[$timestamp] ℹ️  Process count increased by $proc_diff"
        fi
    fi
    
    last_proc_count=$current_proc_count
}

# Function to check for session files being created rapidly
check_session_files() {
    local timestamp=$(get_timestamp)
    local session_files=$(find /tmp -name "*session*" -type f -newer /tmp/session_monitor_marker 2>/dev/null | wc -l)
    
    if [ $session_files -gt 0 ]; then
        echo "[$timestamp] 📁 NEW SESSION FILES: $session_files files created since last check"
        find /tmp -name "*session*" -type f -newer /tmp/session_monitor_marker 2>/dev/null | head -5 | while read file; do
            echo "  ├─ $file"
        done
        if [ $session_files -gt 5 ]; then
            echo "  └─ ... and $((session_files - 5)) more files"
        fi
        echo ""
    fi
    
    # Update marker
    touch /tmp/session_monitor_marker 2>/dev/null
}

# Initialize marker file
touch /tmp/session_monitor_marker 2>/dev/null

# Trap Ctrl+C to clean up
trap 'echo ""; echo "🛑 Monitoring stopped."; rm -f /tmp/session_monitor_marker 2>/dev/null; exit 0' INT

# Initialize variables
last_proc_count=""
zombie_count=0
check_count=0

echo "🚀 Starting monitoring... (checking every 5 seconds)"
echo ""

# Main monitoring loop
while true; do
    check_count=$((check_count + 1))
    
    # Check for zombies every iteration
    if check_zombies; then
        zombie_count=$((zombie_count + 1))
    fi
    
    # Check MCP processes every 3rd iteration (every 15 seconds)
    if [ $((check_count % 3)) -eq 0 ]; then
        check_mcp_processes
    fi
    
    # Monitor process spawning
    monitor_process_spawning
    
    # Check session files every 2nd iteration (every 10 seconds)
    if [ $((check_count % 2)) -eq 0 ]; then
        check_session_files
    fi
    
    # Show summary every 12th iteration (every minute)
    if [ $((check_count % 12)) -eq 0 ]; then
        echo "📊 SUMMARY (last minute): Zombie detections: $zombie_count, Total checks: $check_count"
        zombie_count=0
        echo ""
    fi
    
    sleep 5
done