#!/bin/bash

# FindersKeepers v2 - Setup Zombie Prevention System

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== FindersKeepers v2 Zombie Prevention Setup ===${NC}"
echo

# Create directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p /tmp/fk2-mcp-pids
mkdir -p scripts/systemd

# Make all scripts executable
echo -e "${YELLOW}Making scripts executable...${NC}"
chmod +x scripts/zombie-prevention-wrapper.sh
chmod +x scripts/kill-mcp-process-groups.sh
chmod +x scripts/zombie-monitor-daemon.sh
chmod +x scripts/monitor-zombie-processes.sh
chmod +x scripts/kill-zombie-sessions.sh

echo -e "${GREEN}✓ Scripts prepared${NC}"

# Instructions for systemd setup (requires sudo)
echo
echo -e "${BLUE}=== Instructions for Complete Setup ===${NC}"
echo
echo -e "${YELLOW}1. To run MCP servers with zombie prevention:${NC}"
echo "   ./scripts/zombie-prevention-wrapper.sh python services/mcp-knowledge-server/src/knowledge_server.py"
echo
echo -e "${YELLOW}2. To kill all MCP process groups:${NC}"
echo "   ./scripts/kill-mcp-process-groups.sh"
echo
echo -e "${YELLOW}3. To install the zombie monitor daemon (requires sudo):${NC}"
echo "   sudo cp scripts/systemd/fk2-zombie-monitor.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable fk2-zombie-monitor@$USER"
echo "   sudo systemctl start fk2-zombie-monitor@$USER"
echo
echo -e "${YELLOW}4. To check daemon status:${NC}"
echo "   sudo systemctl status fk2-zombie-monitor@$USER"
echo "   sudo journalctl -u fk2-zombie-monitor@$USER -f"
echo
echo -e "${GREEN}Setup complete! The zombie prevention system is ready.${NC}"