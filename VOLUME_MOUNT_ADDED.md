# Volume Mount Added for FastAPI Development

The following volume mount has been added to the FastAPI service in docker-compose.yml:

```yaml
volumes:
  - ./services/diary-api:/app
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

## What this does:

1. **Live Code Reloading**: Changes to Python files in `/services/diary-api` will be immediately reflected in the container without rebuilding

2. **Persistent Changes**: The MCP integration files (mcp.py, main.py) will persist across container restarts

3. **Development Friendly**: You can edit files locally and see changes immediately

## To Apply:

```bash
cd /media/cain/linux_storage/projects/finderskeepers-v2
docker compose up -d fk2_fastapi
```

This will recreate just the FastAPI container with the new volume mount.

## Note:

- The container runs as root, so files created in the container might have root ownership
- For production, you should still build the image with all files included
- This mount is perfect for development and testing
