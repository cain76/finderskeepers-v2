#!/bin/bash
# MCP N8N Container Manager
# Fixes container proliferation by reusing existing containers with proper fk2_ naming

set -e

CONTAINER_NAME="fk2_mcp_n8n"
IMAGE="ghcr.io/czlonkowski/n8n-mcp:latest"

# Function to check if container exists and is healthy
container_exists_and_healthy() {
    if docker ps -q --filter "name=${CONTAINER_NAME}" | grep -q .; then
        return 0  # Container exists and is running
    elif docker ps -aq --filter "name=${CONTAINER_NAME}" | grep -q .; then
        # Container exists but is stopped - remove it so we can recreate
        echo "Removing stopped container ${CONTAINER_NAME}" >&2
        docker rm "${CONTAINER_NAME}" >&2
        return 1
    else
        return 1  # Container doesn't exist
    fi
}

# Function to start the container
start_container() {
    echo "Starting new MCP container: ${CONTAINER_NAME}" >&2
    docker run -d \
        --name "${CONTAINER_NAME}" \
        --restart unless-stopped \
        -e MCP_MODE=stdio \
        -e LOG_LEVEL=error \
        -e DISABLE_CONSOLE_OUTPUT=true \
        -e N8N_API_URL="${N8N_API_URL:-http://localhost:5678}" \
        -e N8N_API_KEY="${N8N_API_KEY}" \
        "${IMAGE}" >/dev/null
}

# Function to execute MCP commands in the container
execute_mcp() {
    # Execute the MCP server in interactive mode
    docker exec -i "${CONTAINER_NAME}" /usr/local/bin/node /app/dist/index.js
}

# Main logic
if ! container_exists_and_healthy; then
    start_container
    # Give container a moment to start
    sleep 2
fi

# Execute the MCP server
execute_mcp