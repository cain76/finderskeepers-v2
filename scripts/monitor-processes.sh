#!/bin/bash
# FindersKeepers v2 - Process Monitoring Script
# This script monitors for zombie processes and provides health checks

echo "🔍 FindersKeepers v2 Process Monitor"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for zombie processes
echo "🧟 Checking for zombie processes..."
ZOMBIES=$(ps -eo pid,ppid,stat,comm | grep -E "^[[:space:]]*[0-9]+[[:space:]]+[0-9]+[[:space:]]+.*Z" | wc -l)
if [ $ZOMBIES -gt 0 ]; then
    echo "⚠️  Found $ZOMBIES zombie processes:"
    ps -eo pid,ppid,stat,comm | grep -E "^[[:space:]]*[0-9]+[[:space:]]+[0-9]+[[:space:]]+.*Z"
else
    echo "✅ No zombie processes found"
fi

# Check for MCP processes
echo ""
echo "🔗 Checking MCP processes..."
MCP_PROCESSES=$(ps aux | grep -E "mcp|crawl4ai" | grep -v grep | wc -l)
if [ $MCP_PROCESSES -gt 1 ]; then
    echo "⚠️  Found $MCP_PROCESSES MCP processes:"
    ps aux | grep -E "mcp|crawl4ai" | grep -v grep
elif [ $MCP_PROCESSES -eq 1 ]; then
    echo "✅ Found 1 MCP process (expected MCP Knowledge Server):"
    ps aux | grep -E "mcp|crawl4ai" | grep -v grep
else
    echo "✅ No MCP processes found"
fi

# Check Docker containers
echo ""
echo "🐳 Checking Docker containers..."
CONTAINERS=$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "fk2_|finderskeepers")
if [ -n "$CONTAINERS" ]; then
    echo "✅ FindersKeepers containers running:"
    echo "$CONTAINERS"
else
    echo "❌ No FindersKeepers containers found"
fi

# Check for high CPU/memory usage
echo ""
echo "📊 Checking resource usage..."
HIGH_CPU=$(ps aux --sort=-%cpu | head -10 | grep -E "mcp|crawl|finderskeepers" | head -3)
if [ -n "$HIGH_CPU" ]; then
    echo "🔥 High CPU processes:"
    echo "$HIGH_CPU"
else
    echo "✅ No high CPU processes detected"
fi

# Process count
echo ""
echo "📈 Process summary:"
echo "Total processes: $(ps aux | wc -l)"
echo "Zombie processes: $ZOMBIES"
echo "MCP processes: $MCP_PROCESSES"

# Cleanup recommendation
if [ $ZOMBIES -gt 0 ]; then
    echo ""
    echo "🧹 Cleanup recommendations:"
    echo "- Run: docker compose restart"
    echo "- Or: ./scripts/cleanup-zombie-processes.sh"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Process monitoring complete"