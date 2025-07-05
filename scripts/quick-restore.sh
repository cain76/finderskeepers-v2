#!/bin/bash
# FindersKeepers v2 - Quick Data Restore
# Restores from a quick backup

set -e

BACKUP_NAME="$1"

if [ -z "$BACKUP_NAME" ]; then
    echo "❌ Please specify backup name"
    echo "Usage: $0 <backup_name>"
    echo ""
    echo "Available backups:"
    ls -1 backups/ 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_DIR="backups/$BACKUP_NAME"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup not found: $BACKUP_DIR"
    exit 1
fi

echo "🔄 Restoring from backup: $BACKUP_NAME"
echo "⚠️  This will overwrite current data!"
read -p "Continue? (y/N): " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 1
fi

# Stop services
echo "🛑 Stopping services..."
docker compose down

# Function to restore a volume from backup
restore_volume() {
    local volume_name=$1
    local backup_file="$BACKUP_DIR/volumes/${volume_name}.tar.gz"
    
    if [ -f "$backup_file" ]; then
        echo "📦 Restoring volume: $volume_name"
        
        # Remove existing volume
        docker volume rm "$volume_name" 2>/dev/null || true
        
        # Create new volume
        docker volume create "$volume_name"
        
        # Restore data
        docker run --rm \
            -v "$volume_name:/data" \
            -v "$(pwd)/$BACKUP_DIR/volumes:/backup" \
            alpine:latest \
            tar xzf "/backup/${volume_name}.tar.gz" -C /data
        
        echo "✅ Volume $volume_name restored"
    else
        echo "⚠️  Backup file not found: $backup_file"
    fi
}

# Restore all volumes
echo "📁 Restoring volume data..."
VOLUMES=("fk2_n8n_data" "fk2_postgres_data" "fk2_neo4j_data" "fk2_neo4j_logs" "fk2_qdrant_data" "fk2_redis_data" "fk2_ollama_data")

for volume in "${VOLUMES[@]}"; do
    restore_volume "$volume"
done

# Backup current data directory (just in case)
if [ -d "data" ]; then
    echo "💾 Creating safety backup of current data directory..."
    mv data data_backup_$(date +%H%M%S)
fi

# Restore data directory if it exists in backup
if [ -d "$BACKUP_DIR/data" ]; then
    echo "📁 Restoring data directory..."
    cp -r "$BACKUP_DIR/data" ./
fi

# Restore configuration
echo "⚙️  Restoring configuration..."
if [ -d "$BACKUP_DIR/config" ]; then
    cp -r "$BACKUP_DIR/config" ./
fi

# Restore environment file
if [ -f "$BACKUP_DIR/.env.backup" ]; then
    echo "🔧 Restoring environment file..."
    cp "$BACKUP_DIR/.env.backup" ./.env
fi

# Set proper permissions
echo "🔐 Setting permissions..."
if [ -d "data" ]; then
    chmod -R 755 data/
fi
if [ -d "config" ]; then
    chmod -R 755 config/
fi

# Start services
echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "✅ Restore completed!"
echo "📊 Restored from: $BACKUP_DIR"
echo ""
echo "Services starting up... check status with:"
echo "docker compose ps"