#!/bin/bash
# FindersKeepers v2 - Quick Data Backup
# Creates a simple backup of all persistent data

set -e

BACKUP_NAME="${1:-backup_$(date +%Y%m%d_%H%M%S)}"
BACKUP_DIR="backups/$BACKUP_NAME"

echo "🚀 Quick backup starting: $BACKUP_NAME"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Simple volume backup approach - works with Docker volumes
echo "📁 Backing up all persistent data volumes..."

# Create data directory structure in backup
mkdir -p "$BACKUP_DIR/volumes"

# Backup all Docker volumes using the volume backup method
echo "📊 Backing up all databases and data volumes..."
VOLUMES=("fk2_n8n_data" "fk2_postgres_data" "fk2_neo4j_data" "fk2_neo4j_logs" "fk2_qdrant_data" "fk2_redis_data" "fk2_ollama_data")

for volume in "${VOLUMES[@]}"; do
    if docker volume ls --format "{{.Name}}" | grep -q "^${volume}$"; then
        echo "📦 Backing up volume: $volume"
        docker run --rm \
            -v "$volume:/data" \
            -v "$(pwd)/$BACKUP_DIR/volumes:/backup" \
            alpine:latest \
            tar czf "/backup/${volume}.tar.gz" -C /data .
    else
        echo "⚠️  Volume $volume not found, skipping..."
    fi
done

# Also backup any existing data directory if it exists
if [ -d "data" ]; then
    echo "📁 Also backing up data/ directory..."
    cp -r data/ "$BACKUP_DIR/"
fi

# Copy configuration
echo "⚙️  Backing up configuration..."
cp -r config/ "$BACKUP_DIR/"

# Copy logs (last 7 days only to save space)
echo "📋 Backing up recent logs..."
mkdir -p "$BACKUP_DIR/logs"
find logs/ -type f -mtime -7 -exec cp --parents {} "$BACKUP_DIR/" \; 2>/dev/null || true

# Copy environment and compose files
echo "🔧 Backing up environment files..."
cp docker-compose.yml "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/.env.backup" 2>/dev/null || echo "No .env file found"

# Create backup info
cat > "$BACKUP_DIR/backup_info.txt" << EOF
FindersKeepers v2 Backup
========================
Created: $(date)
Type: Quick filesystem backup
Services: All data directories copied
Location: $BACKUP_DIR

Restore Instructions:
1. Stop services: docker compose down
2. Run restore script: ./scripts/quick-restore.sh $BACKUP_NAME
3. Or manually restore volumes:
   - For each volume: docker volume rm <volume_name>
   - Then: docker run --rm -v <volume_name>:/data -v $BACKUP_DIR/volumes:/backup alpine:latest tar xzf /backup/<volume_name>.tar.gz -C /data
4. Start services: docker compose up -d

Total Size: $(du -sh "$BACKUP_DIR" | cut -f1)
EOF

# Calculate size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo ""
echo "✅ Quick backup completed!"
echo "📊 Backup size: $BACKUP_SIZE"
echo "📁 Location: $BACKUP_DIR"
echo ""
echo "To restore: ./scripts/quick-restore.sh $BACKUP_NAME"