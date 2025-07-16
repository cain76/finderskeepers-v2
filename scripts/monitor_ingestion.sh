#!/bin/bash
# Monitor GitHub docs ingestion progress

LOG_FILE="/media/cain/linux_storage/projects/finderskeepers-v2/scripts/github_ingestion.log"

echo "🔍 GitHub Documentation Ingestion Monitor"
echo "=========================================="

# Check if process is running
if pgrep -f "python3 ingest_github_docs.py" > /dev/null; then
    echo "✅ Ingestion process is running"
    
    # Get current progress from log
    CURRENT_FILE=$(grep "Processing.*\.md" "$LOG_FILE" | tail -1 | grep -o '\[[0-9]*/[0-9]*\]' | tr -d '[]')
    if [ ! -z "$CURRENT_FILE" ]; then
        CURRENT=$(echo $CURRENT_FILE | cut -d'/' -f1)
        TOTAL=$(echo $CURRENT_FILE | cut -d'/' -f2)
        PERCENT=$(echo "scale=1; $CURRENT*100/$TOTAL" | bc)
        
        echo "📁 Files processed: $CURRENT/$TOTAL (${PERCENT}%)"
        
        # Calculate estimated completion time
        if [ $CURRENT -gt 0 ]; then
            # Get process start time (rough estimate)
            START_TIME=$(stat -c %Y "$LOG_FILE")
            CURRENT_TIME=$(date +%s)
            ELAPSED=$((CURRENT_TIME - START_TIME))
            
            if [ $ELAPSED -gt 0 ]; then
                RATE=$(echo "scale=2; $CURRENT/$ELAPSED*60" | bc) # files per minute
                REMAINING=$((TOTAL - CURRENT))
                ETA_MINUTES=$(echo "scale=0; $REMAINING/$RATE" | bc)
                ETA_HOURS=$(echo "scale=1; $ETA_MINUTES/60" | bc)
                
                echo "⚡ Processing rate: ${RATE} files/minute"
                echo "⏰ Estimated completion: ${ETA_HOURS} hours (${ETA_MINUTES} minutes)"
            fi
        fi
    fi
    
    # Get database count
    DB_COUNT=$(docker compose exec postgres psql -U finderskeepers -d finderskeepers_v2 -t -c "SELECT COUNT(*) FROM documents WHERE project = 'github-docs';" | tr -d ' ')
    echo "💾 Documents in database: $DB_COUNT"
    
    # Show recent activity
    echo "📋 Recent files processed:"
    tail -5 "$LOG_FILE" | grep "✅ Ingested:" | sed 's/✅ Ingested: /  - /'
    
else
    echo "❌ Ingestion process is not running"
fi

echo ""
echo "📊 Live log tail (last 3 lines):"
tail -3 "$LOG_FILE"