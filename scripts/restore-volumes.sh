#!/bin/bash
# FindersKeepers v2 - Restore Docker Volumes from Backup
# Restores all persistent data from tar backups

set -e

# Use relative path or allow override via environment variable
BACKUP_DIR="${FK2_BACKUP_DIR:-./backups}"

echo "🔄 FindersKeepers v2 Volume Restore Tool"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Get absolute path
BACKUP_DIR_ABS=$(realpath "$BACKUP_DIR")

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR_ABS" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR_ABS"
    exit 1
fi

# List available backups
echo "📦 Available backups:"
TIMESTAMPS=$(ls "$BACKUP_DIR_ABS"/*_*.tar.gz 2>/dev/null | grep -oE '[0-9]{8}_[0-9]{6}' | sort -u || true)

if [ -z "$TIMESTAMPS" ]; then
    echo "❌ No backup files found in $BACKUP_DIR_ABS"
    exit 1
fi

echo "$TIMESTAMPS"

echo ""
echo "🚨 WARNING: This will replace ALL current data!"
echo "Make sure to stop services first: docker compose down"
echo ""

# If timestamp provided as argument, use it
if [ -n "$1" ]; then
    TIMESTAMP="$1"
else
    read -p "Enter timestamp (YYYYMMDD_HHMMSS) to restore: " TIMESTAMP
fi

# Validate timestamp format
if [[ ! $TIMESTAMP =~ ^[0-9]{8}_[0-9]{6}$ ]]; then
    echo "❌ Invalid timestamp format. Use: YYYYMMDD_HHMMSS"
    exit 1
fi

echo ""
echo "🔄 Stopping services..."
docker compose down

# Function to get actual volume name from backup filename
get_volume_name() {
    local service_name=$1
    
    # Map service names to volume names based on current setup
    case "$service_name" in
        "n8n") echo "fk2_n8n_data" ;;
        "postgres") echo "fk2_postgres_data" ;;
        "neo4j") echo "fk2_neo4j_data" ;;
        "neo4j_logs") echo "fk2_neo4j_logs" ;;
        "qdrant") echo "fk2_qdrant_data" ;;
        "redis") echo "fk2_redis_data" ;;
        "ollama") echo "fk2_ollama_data" ;;
        # Handle alternative names
        "n8n_alt") echo "finderskeepers-v2_n8n_data" ;;
        "postgres_alt") echo "finderskeepers-v2_postgres_data" ;;
        "neo4j_alt") echo "finderskeepers-v2_neo4j_data" ;;
        "neo4j_logs_alt") echo "finderskeepers-v2_neo4j_logs" ;;
        "qdrant_alt") echo "finderskeepers-v2_qdrant_data" ;;
        "redis_alt") echo "finderskeepers-v2_redis_data" ;;
        "ollama_alt") echo "finderskeepers-v2_ollama_data" ;;
        *) echo "" ;;
    esac
}

# Function to restore a volume
restore_volume() {
    local backup_file=$1
    local service_name=$(basename "$backup_file" | sed "s/_${TIMESTAMP}.tar.gz//")
    local volume_name=$(get_volume_name "$service_name")
    
    if [ -z "$volume_name" ]; then
        echo "⚠️  Unknown service: $service_name, skipping..."
        return
    fi
    
    echo "📦 Restoring $volume_name from $backup_file..."
    
    # Remove existing volume
    docker volume rm "$volume_name" 2>/dev/null || true
    
    # Create new volume
    docker volume create "$volume_name"
    
    # Restore data
    docker run --rm \
        -v "$volume_name:/data" \
        -v "$BACKUP_DIR_ABS:/backup" \
        alpine:latest \
        tar xzf "/backup/$(basename "$backup_file")" -C /data
    
    echo "✅ $volume_name restored successfully"
}

echo ""
echo "🔄 Restoring all volumes..."

# Find and restore all backup files for the given timestamp
for backup_file in "$BACKUP_DIR_ABS"/*_${TIMESTAMP}.tar.gz; do
    if [ -f "$backup_file" ]; then
        restore_volume "$backup_file"
    fi
done

echo ""
echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All volumes restored successfully!"
echo ""
echo "🎯 Your n8n MCP configuration has been restored!"
echo "🔄 Services are starting up..."
echo ""
echo "⏳ Wait 30 seconds, then check:"
echo "   • n8n: http://localhost:5678"
echo "   • FastAPI: http://localhost:8000"
echo "   • Neo4j: http://localhost:7474"
echo "   • All your workflows and MCP settings should be back!"