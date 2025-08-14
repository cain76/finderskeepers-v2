#!/bin/bash
# Removes the frontend node_modules volume to ensure a clean reinstall of dependencies.
# Usage: ./scripts/prune-frontend-node-modules.sh [project-name]
set -e
PROJECT_NAME=${1:-finderskeepers-v2}
VOLUME_NAME="${PROJECT_NAME}_frontend_node_modules"
if docker volume inspect "$VOLUME_NAME" >/dev/null 2>&1; then
  echo "Removing volume $VOLUME_NAME"
  docker volume rm "$VOLUME_NAME"
else
  echo "Volume $VOLUME_NAME not found. Nothing to remove."
fi

