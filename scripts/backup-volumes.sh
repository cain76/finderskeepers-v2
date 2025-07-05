#!/bin/bash
# FindersKeepers v2 - Backup All Docker Volumes
# Creates tar backups of all persistent data

set -e

# Use relative path or allow override via environment variable
BACKUP_DIR="${FK2_BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🔄 Creating FindersKeepers v2 volume backups..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Get the absolute path for docker mount
BACKUP_DIR_ABS=$(realpath "$BACKUP_DIR")

# Function to backup a volume
backup_volume() {
    local volume_name=$1
    local service_name=$2
    
    echo "📦 Backing up $volume_name..."
    
    # Check if volume exists
    if ! docker volume ls --format "{{.Name}}" | grep -q "^${volume_name}$"; then
        echo "⚠️  Volume $volume_name not found, skipping..."
        return
    fi
    
    # Create a temporary container to access the volume
    docker run --rm \
        -v "$volume_name:/data" \
        -v "$BACKUP_DIR_ABS:/backup" \
        alpine:latest \
        tar czf "/backup/${service_name}_${TIMESTAMP}.tar.gz" -C /data .
    
    echo "✅ $volume_name backed up to ${service_name}_${TIMESTAMP}.tar.gz"
}

# Backup all volumes
echo "🎯 Backing up all FindersKeepers v2 data..."

# Try both possible volume name patterns
backup_volume "fk2_n8n_data" "n8n"
backup_volume "fk2_postgres_data" "postgres"
backup_volume "fk2_neo4j_data" "neo4j"
backup_volume "fk2_neo4j_logs" "neo4j_logs"
backup_volume "fk2_qdrant_data" "qdrant"
backup_volume "fk2_redis_data" "redis"
backup_volume "fk2_ollama_data" "ollama"

# Also try the longer names in case they exist
backup_volume "finderskeepers-v2_n8n_data" "n8n_alt"
backup_volume "finderskeepers-v2_postgres_data" "postgres_alt"
backup_volume "finderskeepers-v2_neo4j_data" "neo4j_alt"
backup_volume "finderskeepers-v2_neo4j_logs" "neo4j_logs_alt"
backup_volume "finderskeepers-v2_qdrant_data" "qdrant_alt"
backup_volume "finderskeepers-v2_redis_data" "redis_alt"
backup_volume "finderskeepers-v2_ollama_data" "ollama_alt"

# Create a manifest file
cat > "$BACKUP_DIR/backup_manifest_${TIMESTAMP}.txt" << EOF
FindersKeepers v2 Backup Manifest
Created: $(date)
Backup Directory: $BACKUP_DIR_ABS

Files Created:
$(ls -la "$BACKUP_DIR"/*_${TIMESTAMP}.tar.gz 2>/dev/null | awk '{print "- " $9}' | xargs -I {} basename {} || echo "Check backup directory for files")

Restore Instructions:
1. Stop services: docker compose down
2. Run restore script: ./scripts/restore-volumes.sh
3. Select this backup timestamp: ${TIMESTAMP}

Your n8n MCP configuration is in the n8n backup!
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All volumes backed up successfully!"
echo ""
echo "📁 Backup location: $BACKUP_DIR"
echo "📋 Manifest file: backup_manifest_${TIMESTAMP}.txt"
echo ""
echo "🎯 Your n8n MCP configuration is safely backed up!"
echo "🔄 To restore, follow instructions in the manifest file."
echo ""
echo "💡 Tip: Run this script regularly for safety!"