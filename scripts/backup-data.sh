#!/bin/bash
# FindersKeepers v2 - Backup All Data
set -e

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
echo "💾 Creating backup: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
echo "📊 Backing up PostgreSQL..."
docker compose exec -T postgres pg_dump -U finderskeepers finderskeepers_v2 > "$BACKUP_DIR/postgres_backup.sql"

# Backup Neo4j
echo "🕸️  Backing up Neo4j..."
docker compose exec -T neo4j neo4j-admin database dump --to-path=/tmp neo4j || {
    echo "⚠️  Neo4j backup failed, trying alternative method..."
    # Alternative: backup the volume directly
    docker run --rm \
        -v fk2_neo4j_data:/data \
        -v "$(pwd)/$BACKUP_DIR:/backup" \
        alpine:latest \
        tar czf /backup/neo4j_volume_backup.tar.gz -C /data .
}

# Get container IDs using docker compose
NEO4J_CONTAINER=$(docker compose ps -q neo4j)
if [ -n "$NEO4J_CONTAINER" ] && [ -f "$NEO4J_CONTAINER:/tmp/neo4j.dump" ]; then
    docker cp "$NEO4J_CONTAINER:/tmp/neo4j.dump" "$BACKUP_DIR/neo4j_backup.dump"
fi

# Backup Qdrant using volume
echo "🔍 Backing up Qdrant..."
docker run --rm \
    -v fk2_qdrant_data:/data \
    -v "$(pwd)/$BACKUP_DIR:/backup" \
    alpine:latest \
    tar czf /backup/qdrant_backup.tar.gz -C /data .

# Backup Redis
echo "🔴 Backing up Redis..."
docker compose exec -T redis redis-cli BGSAVE
sleep 5  # Wait for background save
REDIS_CONTAINER=$(docker compose ps -q redis)
docker cp "$REDIS_CONTAINER:/data/dump.rdb" "$BACKUP_DIR/redis_backup.rdb"

# Backup n8n workflows from volume
echo "🔄 Backing up n8n workflows..."
docker run --rm \
    -v fk2_n8n_data:/data \
    -v "$(pwd)/$BACKUP_DIR:/backup" \
    alpine:latest \
    tar czf /backup/n8n_backup.tar.gz -C /data .

# Backup documents if directory exists
echo "📄 Backing up documents..."
if [ -d "data/documents" ]; then
    tar -czf "$BACKUP_DIR/documents_backup.tar.gz" -C data documents/
else
    echo "⚠️  No documents directory found, skipping..."
fi

# Backup configuration
echo "⚙️  Backing up configuration..."
cp -r config "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/.env.backup" 2>/dev/null || echo "No .env file found"
cp docker-compose.yml "$BACKUP_DIR/"

# Create restore script
cat > "$BACKUP_DIR/restore.sh" << 'EOF'
#!/bin/bash
# Auto-generated restore script
set -e

echo "🔄 Restoring FindersKeepers v2 from backup..."

# Stop services
docker compose down

# Restore PostgreSQL
echo "📊 Restoring PostgreSQL..."
docker compose up -d postgres
sleep 10
docker compose exec -T postgres psql -U finderskeepers -d finderskeepers_v2 < postgres_backup.sql

# Restore Neo4j
echo "🕸️  Restoring Neo4j..."
if [ -f "neo4j_backup.dump" ]; then
    NEO4J_CONTAINER=$(docker compose ps -q neo4j)
    docker cp neo4j_backup.dump "$NEO4J_CONTAINER:/tmp/"
    docker compose exec neo4j neo4j-admin database load --from-path=/tmp neo4j --overwrite-destination
elif [ -f "neo4j_volume_backup.tar.gz" ]; then
    # Stop neo4j and restore volume
    docker compose stop neo4j
    docker volume rm fk2_neo4j_data 2>/dev/null || true
    docker volume create fk2_neo4j_data
    docker run --rm \
        -v fk2_neo4j_data:/data \
        -v "$(pwd):/backup" \
        alpine:latest \
        tar xzf /backup/neo4j_volume_backup.tar.gz -C /data
fi

# Restore Qdrant
echo "🔍 Restoring Qdrant..."
docker compose stop qdrant
docker volume rm fk2_qdrant_data 2>/dev/null || true
docker volume create fk2_qdrant_data
docker run --rm \
    -v fk2_qdrant_data:/data \
    -v "$(pwd):/backup" \
    alpine:latest \
    tar xzf /backup/qdrant_backup.tar.gz -C /data

# Restore Redis
echo "🔴 Restoring Redis..."
docker compose stop redis
REDIS_CONTAINER=$(docker compose ps -q redis)
if [ -n "$REDIS_CONTAINER" ]; then
    docker cp redis_backup.rdb "$REDIS_CONTAINER:/data/dump.rdb"
fi

# Restore n8n
echo "🔄 Restoring n8n..."
docker compose stop n8n
docker volume rm fk2_n8n_data 2>/dev/null || true
docker volume create fk2_n8n_data
docker run --rm \
    -v fk2_n8n_data:/data \
    -v "$(pwd):/backup" \
    alpine:latest \
    tar xzf /backup/n8n_backup.tar.gz -C /data

# Restore documents if backup exists
echo "📄 Restoring documents..."
if [ -f "documents_backup.tar.gz" ]; then
    mkdir -p ../data/documents
    tar -xzf documents_backup.tar.gz -C ../data/
else
    echo "⚠️  No documents backup found, skipping..."
fi

# Restart all services
docker compose up -d

echo "✅ Restore complete!"
EOF

chmod +x "$BACKUP_DIR/restore.sh"

# Create backup info
cat > "$BACKUP_DIR/backup_info.json" << EOF
{
  "backup_date": "$(date -Iseconds)",
  "backup_type": "full",
  "services": ["postgres", "neo4j", "qdrant", "redis", "n8n"],
  "size_mb": $(du -sm "$BACKUP_DIR" | cut -f1),
  "version": "finderskeepers-v2",
  "created_by": "backup-data.sh"
}
EOF

echo ""
echo "✅ Backup completed: $BACKUP_DIR"
echo "📊 Backup size: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo ""
echo "To restore: cd $BACKUP_DIR && ./restore.sh"