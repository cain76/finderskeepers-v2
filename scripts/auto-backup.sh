#!/bin/bash
# FindersKeepers v2 - Automated Backup with Rotation
# Runs backups automatically and manages backup retention

set -e

MAX_BACKUPS=10  # Keep last 10 backups
BACKUP_PREFIX="auto_backup"

echo "🔄 Running automatic backup..."

# Create timestamped backup
BACKUP_NAME="${BACKUP_PREFIX}_$(date +%Y%m%d_%H%M%S)"
./scripts/quick-backup.sh "$BACKUP_NAME"

# Clean up old backups
echo "🧹 Managing backup retention (keeping last $MAX_BACKUPS)..."

# Count auto backups
AUTO_BACKUP_COUNT=$(ls -1 backups/ | grep "^$BACKUP_PREFIX" | wc -l)

if [ "$AUTO_BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    # Calculate how many to delete
    DELETE_COUNT=$((AUTO_BACKUP_COUNT - MAX_BACKUPS))
    
    echo "📦 Found $AUTO_BACKUP_COUNT backups, deleting oldest $DELETE_COUNT..."
    
    # Delete oldest backups
    ls -1t backups/ | grep "^$BACKUP_PREFIX" | tail -n "$DELETE_COUNT" | while read backup; do
        echo "🗑️  Deleting old backup: $backup"
        rm -rf "backups/$backup"
    done
fi

# Show backup summary
echo ""
echo "📊 Backup Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ls -lth backups/ | head -6
echo ""
echo "💾 Total backup space: $(du -sh backups/ | cut -f1)"
echo "🔄 Next auto backup: Add this script to your crontab"
echo ""
echo "To schedule hourly backups:"
echo "crontab -e"
echo "0 * * * * cd $(pwd) && ./scripts/auto-backup.sh >> logs/backup.log 2>&1"