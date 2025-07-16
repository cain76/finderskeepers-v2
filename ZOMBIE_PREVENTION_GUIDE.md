# FindersKeepers v2 - Zombie Process Prevention Guide

## The Problem
The Claude CLI spawns MCP servers but doesn't properly wait() on child processes, causing zombies to accumulate. This is a bug in the Claude CLI's process management.

## Immediate Solutions

### 1. Run the Zombie Monitor (Recommended)
```bash
# Start the monitor in a separate terminal
./scripts/claude-zombie-fix.sh

# This will continuously clean up zombies created by Claude
```

### 2. Kill All Zombies and MCP Processes
```bash
# Nuclear option - kills everything
./scripts/kill-mcp-process-groups.sh
```

### 3. Use the Wrapper for New MCP Servers
When starting MCP servers manually, use:
```bash
./scripts/zombie-prevention-wrapper.sh python services/mcp-knowledge-server/src/knowledge_server.py
```

## Permanent Solutions

### Option 1: Systemd Service (Automatic)
```bash
# Create a systemd service to run the zombie monitor
sudo tee /etc/systemd/system/claude-zombie-fix.service << EOF
[Unit]
Description=Claude CLI Zombie Prevention
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=/media/cain/linux_storage/projects/finderskeepers-v2/scripts/claude-zombie-fix.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable claude-zombie-fix
sudo systemctl start claude-zombie-fix
```

### Option 2: Claude Configuration (If Supported)
Check if Claude has a configuration option to use a wrapper script for MCP servers. If so, configure it to use:
```
/media/cain/linux_storage/projects/finderskeepers-v2/.claude/mcp-wrapper.sh
```

### Option 3: Alias Claude Command
Add to your ~/.bashrc or ~/.zshrc:
```bash
alias claude='(./scripts/claude-zombie-fix.sh &); command claude'
```

## Prevention Best Practices

1. **Always use wrappers** when starting MCP servers manually
2. **Monitor regularly** with `ps aux | grep defunct`
3. **Restart Claude** periodically if zombies accumulate
4. **Report the bug** to Anthropic so they can fix it properly

## Quick Commands

```bash
# Check for zombies
ps aux | grep defunct | grep -v grep

# Count zombies
ps aux | grep defunct | grep -v grep | wc -l

# Find Claude PIDs creating zombies
ps aux | grep defunct | awk '{print $3}' | xargs -I {} ps -p {} -o ppid= | sort | uniq

# Clean everything
./scripts/kill-mcp-process-groups.sh
```

## Root Cause
The Claude CLI needs to:
1. Set up proper SIGCHLD handlers
2. Call wait() or waitpid() on child processes
3. Use double-fork technique for daemon processes
4. Set children to ignore SIGHUP

Until this is fixed in Claude itself, use the monitoring scripts provided.