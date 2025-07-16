#!/bin/bash

# MCP Server wrapper that prevents zombies
# This wrapper ensures proper cleanup when Claude spawns MCP servers

# Enable job control
set -m

# Trap signals for cleanup
cleanup() {
    # Kill all child processes
    jobs -p | xargs -r kill -TERM 2>/dev/null
    wait
    exit
}

trap cleanup EXIT SIGINT SIGTERM

# Start the actual MCP server in background
"$@" &
MCP_PID=$!

# Wait for the MCP server and reap any children
while kill -0 $MCP_PID 2>/dev/null; do
    # Reap any zombie children
    wait -n 2>/dev/null || true
    sleep 1
done

# Final wait to ensure cleanup
wait