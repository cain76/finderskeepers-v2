#!/bin/bash

# Docker Container Backup Script for FindersKeepers v2
# Backs up all essential containers twice weekly with 2-backup rotation
# Designed for Ubuntu 24.04.2 with systemd integration

set -euo pipefail

# Configuration
BACKUP_DIR="/media/cain/linux_storage/projects/backups"
PROJECT_DIR="/media/cain/linux_storage/projects/finderskeepers-v2"
BACKUP_PREFIX="fk2_backup"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="${BACKUP_PREFIX}_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
LOG_FILE="${PROJECT_DIR}/logs/backup_${TIMESTAMP}.log"

# Container names to backup
CONTAINERS=(
    "buildx_buildkit_fast-builder0"
    "fk2_fastapi"
    "fk2_frontend"
    "fk2_n8n"
    "fk2_neo4j"
    "fk2_ollama"
    "fk2_postgres"
    "fk2_qdrant"
    "fk2_redis"
    "portainer"
)

# Volume names (mapped to containers)
declare -A VOLUMES=(
    ["fk2_postgres"]="fk2_postgres_data"
    ["fk2_neo4j"]="fk2_neo4j_data"
    ["fk2_redis"]="fk2_redis_data"
    ["fk2_qdrant"]="fk2_qdrant_data"
    ["fk2_n8n"]="fk2_n8n_data"
    ["fk2_ollama"]="fk2_ollama_data"
    ["portainer"]="portainer_data"
)

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Create backup directory structure
setup_backup_dir() {
    log "Setting up backup directory: $BACKUP_PATH"
    mkdir -p "$BACKUP_PATH"/{volumes,databases,containers,logs}
    mkdir -p "$(dirname "$LOG_FILE")"
}

# Check if container is running
is_container_running() {
    docker ps --format "table {{.Names}}" | tail -n +2 | grep -q "^$1$"
}

# Backup PostgreSQL database
backup_postgres() {
    log "Backing up PostgreSQL database..."
    if is_container_running "fk2_postgres"; then
        docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T postgres pg_dump -U finderskeepers finderskeepers_v2 > "$BACKUP_PATH/databases/postgres_backup.sql"
        log "PostgreSQL backup completed"
    else
        log "WARNING: PostgreSQL container not running, skipping database backup"
    fi
}

# Backup Neo4j database
backup_neo4j() {
    log "Backing up Neo4j database..."
    if is_container_running "fk2_neo4j"; then
        log "Neo4j is running - using volume backup (database cannot be dumped while running)"
        # Neo4j volume backup will be handled in backup_volumes function
        log "Neo4j backup will be completed via volume backup"
    else
        log "WARNING: Neo4j container not running, skipping database backup"
    fi
}

# Backup Redis database
backup_redis() {
    log "Backing up Redis database..."
    if is_container_running "fk2_redis"; then
        # Trigger background save
        docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T redis redis-cli BGSAVE
        sleep 5  # Wait for background save to complete
        # Copy dump file
        docker cp fk2_redis:/data/dump.rdb "$BACKUP_PATH/databases/redis_backup.rdb"
        log "Redis backup completed"
    else
        log "WARNING: Redis container not running, skipping database backup"
    fi
}

# Backup container volumes
backup_volumes() {
    log "Backing up container volumes..."
    for container in "${CONTAINERS[@]}"; do
        if [[ -n "${VOLUMES[$container]:-}" ]]; then
            volume_name="${VOLUMES[$container]}"
            log "Backing up volume: $volume_name"
            
            # Create volume backup using tar
            docker run --rm \
                -v "$volume_name":/data:ro \
                -v "$BACKUP_PATH/volumes":/backup \
                alpine:latest \
                tar czf "/backup/${volume_name}_backup.tar.gz" -C /data . || {
                log "WARNING: Failed to backup volume $volume_name"
            }
        fi
    done
}

# Backup container configurations
backup_configs() {
    log "Backing up container configurations..."
    cp "$PROJECT_DIR/docker-compose.yml" "$BACKUP_PATH/containers/"
    cp "$PROJECT_DIR/.env" "$BACKUP_PATH/containers/" 2>/dev/null || log "WARNING: .env file not found"
    
    # Create container metadata
    for container in "${CONTAINERS[@]}"; do
        if is_container_running "$container"; then
            docker inspect "$container" > "$BACKUP_PATH/containers/${container}_inspect.json"
        fi
    done
}

# Create backup manifest
create_manifest() {
    log "Creating backup manifest..."
    cat > "$BACKUP_PATH/backup_manifest.json" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$TIMESTAMP",
    "containers": [$(printf '"%s",' "${CONTAINERS[@]}" | sed 's/,$//')],
    "volumes": [$(printf '"%s",' "${VOLUMES[@]}" | sed 's/,$//')],
    "backup_path": "$BACKUP_PATH",
    "created_by": "docker-backup.sh",
    "system": "Ubuntu 24.04.2",
    "restore_script": "docker-restore.sh"
}
EOF
}

# Rotate backups (keep 2 most recent)
rotate_backups() {
    log "Rotating backups..."
    cd "$BACKUP_DIR"
    
    # Get list of backup directories, sorted by modification time
    backups=($(ls -1t | grep "^${BACKUP_PREFIX}_" | head -n 10))
    
    # Keep only 2 most recent backups
    if [ ${#backups[@]} -gt 2 ]; then
        log "Found ${#backups[@]} backups, keeping 2 most recent"
        for ((i=2; i<${#backups[@]}; i++)); do
            log "Removing old backup: ${backups[$i]}"
            rm -rf "${backups[$i]}"
        done
    fi
}

# Compress final backup
compress_backup() {
    log "Compressing backup..."
    cd "$BACKUP_DIR"
    tar czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
    rm -rf "$BACKUP_NAME"
    log "Backup compressed to ${BACKUP_NAME}.tar.gz"
}

# Main backup process
main() {
    log "Starting Docker backup process..."
    log "Backup name: $BACKUP_NAME"
    
    # Setup
    setup_backup_dir
    
    # Backup databases with specific tools
    backup_postgres
    backup_neo4j
    backup_redis
    
    # Backup volumes
    backup_volumes
    
    # Backup configurations
    backup_configs
    
    # Create manifest
    create_manifest
    
    # Compress backup
    compress_backup
    
    # Rotate old backups
    rotate_backups
    
    # Final stats
    backup_size=$(du -sh "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)
    log "Backup completed successfully"
    log "Backup size: $backup_size"
    log "Backup location: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    log "Log file: $LOG_FILE"
}

# Run backup
main "$@"