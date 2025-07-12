#!/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/.venv/bin/python
"""
FindersKeepers v2 - Zombie Session Cleanup
Marks all long-running "active" sessions as ended to prevent resource leaks
"""

import asyncio
import httpx
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZombieSessionCleaner:
    def __init__(self):
        self.fastapi_base_url = os.getenv("FASTAPI_URL", "http://localhost:8000")
        self.n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678")
        
    async def get_all_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all sessions marked as active from the database"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.fastapi_base_url}/api/diary/sessions/list",
                    params={
                        "limit": 1000  # Get all sessions
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    sessions = data.get("data", [])
                    # Filter for active sessions only
                    active_sessions = [s for s in sessions if s.get("status") != "ended"]
                    logger.info(f"Found {len(active_sessions)} active sessions out of {len(sessions)} total")
                    return active_sessions
                else:
                    logger.error(f"Failed to fetch sessions: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching active sessions: {e}")
            return []
    
    async def mark_session_ended(self, session_id: str, reason: str = "cleanup_zombie") -> bool:
        """Mark a specific session as ended using FastAPI endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.fastapi_base_url}/api/diary/sessions/{session_id}/end",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Marked session {session_id[:8]}... as ended")
                    return True
                else:
                    logger.warning(f"⚠️  Failed to mark session {session_id[:8]}... as ended: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error marking session {session_id[:8]}... as ended: {e}")
            return False
    
    async def identify_zombie_sessions(self, sessions: List[Dict[str, Any]], max_age_hours: int = 6) -> List[Dict[str, Any]]:
        """Identify sessions that should be considered zombies"""
        zombies = []
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        for session in sessions:
            try:
                # Parse the start time - check both possible field names
                start_time_str = session.get("session_start") or session.get("started_at", "")
                if not start_time_str:
                    logger.warning(f"No session_start/started_at for session {session.get('session_id', 'unknown')[:8]}...")
                    continue
                    
                
                # Handle different datetime formats
                try:
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                except Exception as e1:
                    try:
                        # Try alternative parsing
                        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                    except Exception as e2:
                        try:
                            # Try another format
                            start_time = datetime.strptime(start_time_str, "%m/%d/%Y, %I:%M:%S %p")
                        except Exception as e3:
                            logger.warning(f"Could not parse datetime '{start_time_str}': {e1}, {e2}, {e3}")
                            # If we can't parse the time, assume it's old and mark as zombie
                            zombies.append({
                                **session,
                                "age_hours": float('inf')
                            })
                            continue
                
                # Remove timezone info for comparison (assume UTC)
                if start_time.tzinfo:
                    start_time = start_time.replace(tzinfo=None)
                
                age_hours = (datetime.utcnow() - start_time).total_seconds() / 3600
                
                if start_time < cutoff_time:
                    zombies.append({
                        **session,
                        "age_hours": age_hours
                    })
                    
            except Exception as e:
                logger.warning(f"Error parsing session {session.get('session_id', 'unknown')[:8]}...: {e}")
                # If we can't parse the time, assume it's old and mark as zombie
                zombies.append({
                    **session,
                    "age_hours": float('inf')
                })
        
        return zombies
    
    async def cleanup_zombies(self, dry_run: bool = False, max_age_hours: int = 6) -> Dict[str, Any]:
        """Main cleanup function"""
        logger.info(f"🧹 Starting zombie session cleanup (dry_run={dry_run}, max_age={max_age_hours}h)")
        
        # Get all active sessions
        active_sessions = await self.get_all_active_sessions()
        if not active_sessions:
            return {"total_sessions": 0, "zombies_found": 0, "cleaned": 0}
        
        # Identify zombies
        zombies = await self.identify_zombie_sessions(active_sessions, max_age_hours)
        
        logger.info(f"📊 Analysis:")
        logger.info(f"   Total active sessions: {len(active_sessions)}")
        logger.info(f"   Zombie sessions (>{max_age_hours}h old): {len(zombies)}")
        
        if not zombies:
            logger.info("✅ No zombie sessions found!")
            return {
                "total_sessions": len(active_sessions),
                "zombies_found": 0,
                "cleaned": 0
            }
        
        # Show zombie details
        logger.info(f"🧟 Zombie sessions to clean:")
        for zombie in zombies[:10]:  # Show first 10
            age = zombie.get("age_hours", 0)
            agent_type = zombie.get("agent_type", "unknown")
            session_id = zombie.get("session_id", "unknown")[:8]
            logger.info(f"   {session_id}... ({agent_type}) - {age:.1f}h old")
        
        if len(zombies) > 10:
            logger.info(f"   ... and {len(zombies) - 10} more")
        
        if dry_run:
            logger.info("🔍 DRY RUN - Would clean these sessions but not actually doing it")
            return {
                "total_sessions": len(active_sessions),
                "zombies_found": len(zombies),
                "cleaned": 0,
                "dry_run": True
            }
        
        # Actually clean the zombies
        logger.info("🧹 Cleaning zombie sessions...")
        cleaned_count = 0
        
        for zombie in zombies:
            session_id = zombie.get("session_id")
            if not session_id:
                continue
                
            success = await self.mark_session_ended(session_id, "cleanup_zombie_batch")
            if success:
                cleaned_count += 1
            
            # Small delay to avoid overwhelming the API
            await asyncio.sleep(0.1)
        
        logger.info(f"✅ Cleanup complete!")
        logger.info(f"   Zombies found: {len(zombies)}")
        logger.info(f"   Successfully cleaned: {cleaned_count}")
        logger.info(f"   Failed to clean: {len(zombies) - cleaned_count}")
        
        return {
            "total_sessions": len(active_sessions),
            "zombies_found": len(zombies),
            "cleaned": cleaned_count,
            "failed": len(zombies) - cleaned_count
        }

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up zombie MCP sessions")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned without actually cleaning")
    parser.add_argument("--max-age", type=int, default=6, help="Maximum age in hours before considering a session zombie (default: 6)")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    cleaner = ZombieSessionCleaner()
    
    if not args.dry_run and not args.force:
        print("⚠️  This will mark old active sessions as ended in the database.")
        print(f"   Sessions older than {args.max_age} hours will be cleaned.")
        response = input("   Continue? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    result = await cleaner.cleanup_zombies(
        dry_run=args.dry_run,
        max_age_hours=args.max_age
    )
    
    print("\n📊 Summary:")
    print(f"   Total active sessions: {result['total_sessions']}")
    print(f"   Zombie sessions found: {result['zombies_found']}")
    
    if result.get('dry_run'):
        print(f"   Would clean: {result['zombies_found']} sessions")
    else:
        print(f"   Successfully cleaned: {result['cleaned']}")
        if result.get('failed', 0) > 0:
            print(f"   Failed to clean: {result['failed']}")

if __name__ == "__main__":
    asyncio.run(main())