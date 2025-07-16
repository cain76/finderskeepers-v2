#!/bin/bash
# FindersKeepers v2 - Zombie Process Cleanup Script
# This script safely cleans up zombie processes

echo "🧹 FindersKeepers v2 Zombie Process Cleanup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for zombie processes
ZOMBIES=$(ps -eo pid,ppid,stat,comm | grep -E "^[[:space:]]*[0-9]+[[:space:]]+[0-9]+[[:space:]]+.*Z" | wc -l)
if [ $ZOMBIES -eq 0 ]; then
    echo "✅ No zombie processes found - system is clean"
    exit 0
fi

echo "⚠️  Found $ZOMBIES zombie processes"

# List zombie processes
echo ""
echo "🧟 Zombie processes:"
ps -eo pid,ppid,stat,comm | grep -E "^[[:space:]]*[0-9]+[[:space:]]+[0-9]+[[:space:]]+.*Z"

# Get parent processes of zombies
echo ""
echo "🔍 Identifying parent processes..."
PARENT_PIDS=$(ps -eo pid,ppid,stat,comm | grep -E "^[[:space:]]*[0-9]+[[:space:]]+[0-9]+[[:space:]]+.*Z" | awk '{print $2}' | sort -u)

if [ -n "$PARENT_PIDS" ]; then
    echo "📝 Parent processes to restart:"
    for PID in $PARENT_PIDS; do
        ps aux | grep -E "^[^ ]+ +$PID " | grep -v grep
    done
    
    echo ""
    echo "🔄 Restarting Docker containers to clean up zombies..."
    docker compose restart
    
    echo ""
    echo "⏳ Waiting for services to restart..."
    sleep 10
    
    # Check if zombies are gone
    NEW_ZOMBIES=$(ps -eo pid,ppid,stat,comm | grep -E "^[[:space:]]*[0-9]+[[:space:]]+[0-9]+[[:space:]]+.*Z" | wc -l)
    if [ $NEW_ZOMBIES -eq 0 ]; then
        echo "✅ All zombie processes cleaned up successfully"
    else
        echo "⚠️  Still $NEW_ZOMBIES zombie processes remaining"
        echo "Consider running: sudo reboot"
    fi
else
    echo "❌ Could not identify parent processes"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧹 Zombie cleanup complete"