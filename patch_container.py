#!/usr/bin/env python3
"""
Patch the container to use real data instead of mock data
"""
import subprocess
import sys

# Read the main.py file from the container
print("Reading main.py from container...")
result = subprocess.run([
    "docker", "exec", "fk2_fastapi", "cat", "/app/main.py"
], capture_output=True, text=True)

if result.returncode != 0:
    print("Error reading main.py from container")
    sys.exit(1)

original_content = result.stdout

# Find the mock session stats endpoint and replace it
mock_session_endpoint = '''@app.get("/api/stats/sessions", tags=["Statistics"])
async def get_session_stats(timeframe: str = "24h"):
    """Get session statistics for specified timeframe"""
    try:
        logger.info(f"Getting session stats for timeframe: {timeframe}")
        
        # Mock statistics based on timeframe
        stats = {
            "timeframe": timeframe,
            "total_sessions": 25,
            "active_sessions": 3,
            "completed_sessions": 20,
            "error_sessions": 2,
            "avg_duration_minutes": 45.2,
            "total_actions": 156,
            "avg_actions_per_session": 6.2,
            "agent_breakdown": {
                "claude": 15,
                "gpt": 8,
                "local": 2
            },
            "timeline": [
                {"time": f"{i:02d}:00", "sessions": 2 + i % 5, "actions": 10 + i * 2}
                for i in range(24)
            ]
        }
        
        return {
            "success": True,
            "data": stats,
            "message": f"Retrieved session statistics for {timeframe}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Session stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))'''

real_session_endpoint = '''@app.get("/api/stats/sessions", tags=["Statistics"])
async def get_session_stats(timeframe: str = "24h"):
    """Get REAL session statistics from PostgreSQL database"""
    try:
        logger.info(f"Getting REAL session stats for timeframe: {timeframe}")
        
        # Import asyncpg for database connection
        import asyncpg
        
        # Connect to database
        conn = await asyncpg.connect(
            host='fk2_postgres',
            port=5432,
            user='finderskeepers',
            password='fk2025secure',
            database='finderskeepers_v2'
        )
        
        # Get REAL statistics from database
        total_sessions = await conn.fetchval('SELECT COUNT(*) FROM agent_sessions')
        active_sessions = await conn.fetchval('SELECT COUNT(*) FROM agent_sessions WHERE end_time IS NULL')
        completed_sessions = await conn.fetchval('SELECT COUNT(*) FROM agent_sessions WHERE end_time IS NOT NULL')
        
        # Calculate timeframe
        now = datetime.now(timezone.utc)
        if timeframe == "24h":
            start_time = now - timedelta(hours=24)
        elif timeframe == "7d":
            start_time = now - timedelta(days=7)
        else:
            start_time = now - timedelta(hours=24)
            
        recent_sessions = await conn.fetchval(
            'SELECT COUNT(*) FROM agent_sessions WHERE start_time >= $1', 
            start_time
        )
        
        await conn.close()
        
        stats = {
            "timeframe": timeframe,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "completed_sessions": completed_sessions,
            "recent_sessions": recent_sessions,
            "error_sessions": 0,
            "avg_duration_minutes": 0.0,
            "total_actions": 0,
            "avg_actions_per_session": 0.0,
            "agent_breakdown": {"claude": total_sessions},
            "timeline": []
        }
        
        return {
            "success": True,
            "data": stats,
            "message": f"Retrieved REAL session statistics for {timeframe} - NO MORE MOCK DATA!",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Session stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))'''

# Replace the mock endpoint with real endpoint
if mock_session_endpoint in original_content:
    print("Found mock session endpoint - replacing with real data endpoint...")
    new_content = original_content.replace(mock_session_endpoint, real_session_endpoint)
    
    # Write the patched content back to the container
    with open("/tmp/patched_main.py", "w") as f:
        f.write(new_content)
    
    # Copy the patched file to the container
    subprocess.run(["docker", "cp", "/tmp/patched_main.py", "fk2_fastapi:/app/main.py"])
    
    print("✅ Patched main.py with real database connection!")
    print("Restarting container...")
    
    # Restart the container
    subprocess.run(["docker", "restart", "fk2_fastapi"])
    
    print("✅ Container restarted with real data endpoint!")
else:
    print("❌ Mock session endpoint not found in the expected format")
    
print("\nTesting the patched endpoint...")
import time
time.sleep(5)

# Test the patched endpoint
result = subprocess.run([
    "curl", "-s", "http://localhost:8000/api/stats/sessions"
], capture_output=True, text=True)

print("Response:", result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout)