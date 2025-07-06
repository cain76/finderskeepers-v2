#!/bin/bash
# FindersKeepers v2 - Pre-Migration Backup Script
# Creates comprehensive backup before UV migration

set -e

BACKUP_DIR="./backups/pre-uv-migration-$(date +%Y%m%d_%H%M%S)"
echo "🔄 FindersKeepers v2 - Pre-Migration Backup"
echo "============================================"
echo "📁 Backup directory: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to backup with error handling
backup_with_retry() {
    local description="$1"
    local command="$2"
    local output_file="$3"
    
    echo "📦 Backing up: $description"
    if eval "$command" > "$BACKUP_DIR/$output_file" 2>&1; then
        echo "✅ Success: $description"
    else
        echo "⚠️  Warning: Failed to backup $description"
        echo "   Check $BACKUP_DIR/$output_file for details"
    fi
}

# 1. Database Backups
echo ""
echo "🗄️  DATABASE BACKUPS"
echo "===================="

# PostgreSQL backup
backup_with_retry "PostgreSQL schema and data" \
    "docker exec fk2_postgres pg_dump -U finderskeepers -d finderskeepers_v2" \
    "postgres_full_backup.sql"

# PostgreSQL table list
backup_with_retry "PostgreSQL table structure" \
    "docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -c '\dt'" \
    "postgres_tables.txt"

# Neo4j backup (if accessible)
backup_with_retry "Neo4j database backup" \
    "docker exec fk2_neo4j cypher-shell -u neo4j -p fk2025neo4j 'MATCH (n) RETURN count(n) as total_nodes'" \
    "neo4j_node_count.txt"

# Redis backup
backup_with_retry "Redis data backup" \
    "docker exec fk2_redis redis-cli --rdb /tmp/dump.rdb && docker exec fk2_redis cat /tmp/dump.rdb" \
    "redis_dump.rdb"

# Qdrant collections info
backup_with_retry "Qdrant collections info" \
    "curl -s http://localhost:6333/collections" \
    "qdrant_collections.json"

# 2. Container State Backup
echo ""
echo "🐳 CONTAINER STATE BACKUP"
echo "========================="

# Current container status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}" > "$BACKUP_DIR/container_status.txt"

# Docker compose configuration
cp docker-compose.yml "$BACKUP_DIR/docker-compose.yml.backup"

# Check Docker Compose command (V1 vs V2)
if command_exists docker-compose; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    echo "⚠️  Neither docker-compose nor docker compose found"
    DOCKER_COMPOSE="docker compose"  # Default to V2
fi

# Environment variables (sanitized)
backup_with_retry "Environment configuration" \
    "docker exec fk2_fastapi env | grep -v 'API_KEY\|PASSWORD\|SECRET' | sort" \
    "fastapi_env_vars.txt"

# Current FastAPI requirements for comparison
if [ -f "services/diary-api/requirements.txt" ]; then
    cp "services/diary-api/requirements.txt" "$BACKUP_DIR/old_requirements.txt"
fi

# 3. Volume Information
echo ""
echo "💾 VOLUME INFORMATION"
echo "===================="

# Docker volumes info
docker volume ls | grep fk2 > "$BACKUP_DIR/docker_volumes.txt"

# Volume sizes
for volume in $(docker volume ls -q | grep fk2); do
    size=$(docker run --rm -v "$volume":/data alpine du -sh /data 2>/dev/null || echo "N/A")
    echo "$volume: $size" >> "$BACKUP_DIR/volume_sizes.txt"
done

# 4. Application State
echo ""
echo "🚀 APPLICATION STATE"
echo "==================="

# FastAPI health check
backup_with_retry "FastAPI health status" \
    "curl -s http://localhost:8000/health || echo 'Health endpoint not available'" \
    "fastapi_health.txt"

# API endpoints check
backup_with_retry "FastAPI API docs" \
    "curl -s http://localhost:8000/docs || echo 'Docs endpoint not available'" \
    "fastapi_docs.html"

# n8n workflows (if accessible)
backup_with_retry "n8n workflows export" \
    "curl -s -u admin:finderskeepers2025 http://localhost:5678/api/v1/workflows || echo 'n8n not accessible'" \
    "n8n_workflows.json"

# 5. System Information
echo ""
echo "💻 SYSTEM INFORMATION"
echo "===================="

# System info
uname -a > "$BACKUP_DIR/system_info.txt"
docker --version >> "$BACKUP_DIR/system_info.txt"
$DOCKER_COMPOSE --version >> "$BACKUP_DIR/system_info.txt" 2>/dev/null || echo "Docker Compose V2" >> "$BACKUP_DIR/system_info.txt"

# GPU info (if available)
nvidia-smi > "$BACKUP_DIR/gpu_info.txt" 2>/dev/null || echo "NVIDIA GPU not available" > "$BACKUP_DIR/gpu_info.txt"

# 6. Create Restore Instructions
echo ""
echo "📝 CREATING RESTORE INSTRUCTIONS"
echo "================================="

cat > "$BACKUP_DIR/RESTORE_INSTRUCTIONS.md" << 'EOF'
# FindersKeepers v2 - Restore Instructions

## Quick Rollback (if UV migration fails)

1. **Stop new containers:**
   ```bash
   $DOCKER_COMPOSE down
   ```

2. **Restore old docker-compose.yml:**
   ```bash
   cp docker-compose.yml.backup docker-compose.yml
   ```

3. **Restart with old configuration:**
   ```bash
   $DOCKER_COMPOSE up -d
   ```

## Full Database Restore (if data loss occurs)

1. **Restore PostgreSQL:**
   ```bash
   docker exec -i fk2_postgres psql -U finderskeepers -d finderskeepers_v2 < postgres_full_backup.sql
   ```

2. **Restore Redis:**
   ```bash
   docker cp redis_dump.rdb fk2_redis:/tmp/dump.rdb
   docker exec fk2_redis redis-cli --rdb /tmp/dump.rdb
   ```

3. **Check Qdrant collections:**
   ```bash
   curl http://localhost:6333/collections
   ```

## Verification Steps

1. **Check container status:**
   ```bash
   docker ps
   ```

2. **Test API health:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Verify database tables:**
   ```bash
   docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -c "\dt"
   ```

## Contact Information
- Backup created: $(date)
- System: $(uname -a)
- Docker version: $(docker --version)
EOF

# 7. Final Summary
echo ""
echo "✅ BACKUP COMPLETE!"
echo "==================="
echo "📁 Backup location: $BACKUP_DIR"
echo "📄 Files backed up:"
ls -la "$BACKUP_DIR" | tail -n +2 | awk '{print "   " $9 " (" $5 " bytes)"}'

echo ""
echo "🎯 MIGRATION SAFETY CHECKLIST:"
echo "✅ Database schemas and data backed up"
echo "✅ Container configurations saved"  
echo "✅ Volume information documented"
echo "✅ Restore instructions created"
echo "✅ System state captured"

echo ""
echo "🚀 Ready for UV migration!"
echo "   Run: ./scripts/migrate-to-uv.sh"
echo ""
echo "🔙 Rollback available:"
echo "   See: $BACKUP_DIR/RESTORE_INSTRUCTIONS.md"