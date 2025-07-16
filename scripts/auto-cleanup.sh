#!/bin/bash
# Auto-cleanup script for FindersKeepers v2
# Run this before starting new claude-code sessions

echo "🧹 Auto-cleaning zombie sessions..."
cd "$(dirname "$0")/.."
./scripts/cleanup-zombie-sessions.py --max-age 1 --force > /dev/null 2>&1
echo "✅ Sessions cleaned! Ready for new session."