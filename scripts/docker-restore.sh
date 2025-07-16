#!/bin/bash

# Docker Container Restore Script for FindersKeepers v2
# Restores containers from backup files created by docker-backup.sh

set -euo pipefail

# Configuration
BACKUP_DIR="/media/cain/linux_storage/projects/backups"
PROJECT_DIR="/media/cain/linux_storage/projects/finderskeepers-v2"
LOG_FILE="${PROJECT_DIR}/logs/restore_$(date +%Y%m%d_%H%M%S).log"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Usage function
usage() {
    echo "Usage: $0 [backup_name]"
    echo ""
    echo "Available backups:"
    ls -1 "$BACKUP_DIR" | grep "^fk2_backup_" | sort -r | head -10
    echo ""
    echo "Or use compressed backup:"
    ls -1 "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -10 || echo "No compressed backups found"
    exit 1
}

# Check if backup exists
check_backup() {
    local backup_name="$1"
    local backup_path=""
    
    # Check if it's a compressed backup
    if [[ "$backup_name" == *.tar.gz ]]; then
        backup_path="$BACKUP_DIR/$backup_name"
        if [[ ! -f "$backup_path" ]]; then
            error_exit "Compressed backup not found: $backup_path"
        fi
        # Extract compressed backup
        log "Extracting compressed backup: $backup_name"
        cd "$BACKUP_DIR"
        tar xzf "$backup_name"
        backup_name="${backup_name%.tar.gz}"
    fi
    
    # Check directory backup
    backup_path="$BACKUP_DIR/$backup_name"
    if [[ ! -d "$backup_path" ]]; then
        error_exit "Backup directory not found: $backup_path"
    fi
    
    echo "$backup_path"
}

# Stop containers
stop_containers() {
    log "Stopping containers..."
    cd "$PROJECT_DIR"
    docker compose down || log "WARNING: Some containers may not have stopped cleanly"
}

# Restore PostgreSQL database
restore_postgres() {
    local backup_path="$1"
    local postgres_backup="$backup_path/databases/postgres_backup.sql"
    
    log "Restoring PostgreSQL database..."
    if [[ -f "$postgres_backup" ]]; then
        # Start only postgres container
        docker compose up -d postgres
        sleep 10  # Wait for postgres to be ready
        
        # Restore database
        docker compose exec -T postgres dropdb -U finderskeepers finderskeepers_v2 || log "Database may not exist"
        docker compose exec -T postgres createdb -U finderskeepers finderskeepers_v2
        docker compose exec -T postgres psql -U finderskeepers finderskeepers_v2 < "$postgres_backup"
        log "PostgreSQL database restored"
    else
        log "WARNING: PostgreSQL backup not found, skipping database restore"
    fi
}

# Restore Redis database
restore_redis() {
    local backup_path="$1"
    local redis_backup="$backup_path/databases/redis_backup.rdb"
    
    log "Restoring Redis database..."
    if [[ -f "$redis_backup" ]]; then
        # Start only redis container
        docker compose up -d redis
        sleep 5
        
        # Stop redis, copy dump file, restart redis
        docker compose stop redis
        docker cp "$redis_backup" fk2_redis:/data/dump.rdb
        docker compose start redis
        log "Redis database restored"
    else
        log "WARNING: Redis backup not found, skipping database restore"
    fi
}

# Restore volumes
restore_volumes() {
    local backup_path="$1"
    local volumes_dir="$backup_path/volumes"
    
    log "Restoring container volumes..."
    if [[ -d "$volumes_dir" ]]; then
        for volume_backup in "$volumes_dir"/*.tar.gz; do
            if [[ -f "$volume_backup" ]]; then
                local volume_name=$(basename "$volume_backup" _backup.tar.gz)
                log "Restoring volume: $volume_name"
                
                # Remove existing volume
                docker volume rm "$volume_name" 2>/dev/null || log "Volume $volume_name may not exist"
                
                # Create new volume
                docker volume create "$volume_name"
                
                # Restore volume data
                docker run --rm \
                    -v "$volume_name":/data \
                    -v "$volumes_dir":/backup \
                    alpine:latest \
                    tar xzf "/backup/$(basename "$volume_backup")" -C /data
                
                log "Volume $volume_name restored"
            fi
        done
    else
        log "WARNING: No volume backups found"
    fi
}

# Start all containers
start_containers() {
    log "Starting all containers..."
    cd "$PROJECT_DIR"
    docker compose up -d
    log "All containers started"
}

# Main restore process
main() {
    if [[ $# -eq 0 ]]; then
        usage
    fi
    
    local backup_name="$1"
    
    log "Starting restore process for backup: $backup_name"
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Check backup exists
    local backup_path
    backup_path=$(check_backup "$backup_name")
    
    log "Using backup: $backup_path"
    
    # Confirm restore
    echo "WARNING: This will stop all containers and restore from backup."
    echo "Current data will be LOST!"
    echo "Backup: $backup_path"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [[ "$confirm" != "yes" ]]; then
        log "Restore cancelled by user"
        exit 0
    fi
    
    # Stop containers
    stop_containers
    
    # Restore volumes first
    restore_volumes "$backup_path"
    
    # Restore databases
    restore_postgres "$backup_path"
    restore_redis "$backup_path"
    
    # Start all containers
    start_containers
    
    log "Restore completed successfully!"
    log "Log file: $LOG_FILE"
}

# Run restore
main "$@"