#!/usr/bin/env python3
"""
Fix the import issue in the container
"""
import subprocess

# Add the missing import to the main.py file
print("Adding missing timedelta import...")

# Read the current main.py
result = subprocess.run([
    "docker", "exec", "fk2_fastapi", "cat", "/app/main.py"
], capture_output=True, text=True)

content = result.stdout

# Find the datetime import line and add timedelta
if "from datetime import datetime, timezone" in content:
    print("Found datetime import, adding timedelta...")
    new_content = content.replace(
        "from datetime import datetime, timezone",
        "from datetime import datetime, timezone, timedelta"
    )
    
    # Write the fixed content
    with open("/tmp/fixed_main.py", "w") as f:
        f.write(new_content)
    
    # Copy back to container
    subprocess.run(["docker", "cp", "/tmp/fixed_main.py", "fk2_fastapi:/app/main.py"])
    
    print("✅ Fixed imports!")
    print("Restarting container...")
    
    # Restart the container
    subprocess.run(["docker", "restart", "fk2_fastapi"])
    
    print("✅ Container restarted!")
else:
    print("❌ Could not find datetime import line")
    
print("\nTesting fixed endpoint...")
import time
time.sleep(5)

# Test the fixed endpoint
result = subprocess.run([
    "curl", "-s", "http://localhost:8000/api/stats/sessions"
], capture_output=True, text=True)

print("Response:", result.stdout[:300] + "..." if len(result.stdout) > 300 else result.stdout)