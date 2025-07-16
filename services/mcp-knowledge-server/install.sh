#!/bin/bash
"""
FindersKeepers v2 MCP Knowledge Server Installation Script

This script sets up the MCP Knowledge Server on a new client with all dependencies
and proper configuration. It handles virtual environments, dependencies, and
provides setup verification.
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SERVER_DIR/.venv"
PYTHON_MIN_VERSION="3.11"

echo -e "${BLUE}🚀 FindersKeepers v2 MCP Knowledge Server Installer${NC}"
echo -e "${BLUE}===================================================${NC}"
echo ""

# Function to print colored output
print_step() {
    echo -e "${PURPLE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to compare version numbers
version_ge() {
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# Step 1: Check Python version
print_step "Checking Python installation..."

if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
print_success "Found Python $PYTHON_VERSION"

if ! version_ge "$PYTHON_VERSION" "$PYTHON_MIN_VERSION"; then
    print_error "Python $PYTHON_MIN_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

# Step 2: Create virtual environment
print_step "Setting up virtual environment..."

if [ -d "$VENV_DIR" ]; then
    print_warning "Virtual environment already exists. Removing old environment..."
    rm -rf "$VENV_DIR"
fi

python3 -m venv "$VENV_DIR"
print_success "Virtual environment created at $VENV_DIR"

# Step 3: Activate virtual environment and upgrade pip
print_step "Activating virtual environment and upgrading pip..."

source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel
print_success "Virtual environment activated and pip upgraded"

# Step 4: Install dependencies
print_step "Installing MCP Knowledge Server dependencies..."

# Install the server in development mode
pip install -e "$SERVER_DIR"
print_success "Core dependencies installed"

# Install development dependencies if requested
if [ "$1" = "--dev" ] || [ "$1" = "-d" ]; then
    print_step "Installing development dependencies..."
    pip install -e "$SERVER_DIR[dev]"
    print_success "Development dependencies installed"
fi

# Step 5: Create environment configuration template
print_step "Creating environment configuration..."

ENV_FILE="$SERVER_DIR/.env"
ENV_TEMPLATE="$SERVER_DIR/.env.template"

cat > "$ENV_TEMPLATE" << 'EOF'
# FindersKeepers v2 MCP Knowledge Server Configuration
# Copy this file to .env and adjust the values for your environment

# PostgreSQL Configuration (Docker containers)
POSTGRES_URL=postgresql://finderskeepers:fk2025secure@fk2_postgres:5432/finderskeepers_v2
POSTGRES_HOST=fk2_postgres
POSTGRES_PORT=5432
POSTGRES_USER=finderskeepers
POSTGRES_PASSWORD=fk2025secure
POSTGRES_DB=finderskeepers_v2

# Neo4j Configuration (Docker containers)
NEO4J_URL=bolt://fk2_neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=fk2025neo4j

# Qdrant Vector Database (Docker containers)
QDRANT_URL=http://fk2_qdrant:6333

# Redis Cache (Docker containers)
REDIS_URL=redis://fk2_redis:6379
REDIS_HOST=fk2_redis
REDIS_PORT=6379

# FastAPI Backend (Docker containers)
FASTAPI_URL=http://fk2_fastapi:8000

# n8n Automation (Docker containers)
N8N_WEBHOOK_URL=http://fk2_n8n:5678

# AI API Keys (optional - for enhanced features)
# OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here
# GOOGLE_API_KEY=your_google_key_here

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=structured

# Session Management
HEARTBEAT_INTERVAL=30
TIMEOUT_THRESHOLD=90
EOF

if [ ! -f "$ENV_FILE" ]; then
    cp "$ENV_TEMPLATE" "$ENV_FILE"
    print_success "Environment configuration created: $ENV_FILE"
    print_warning "Please edit $ENV_FILE with your database connection details"
else
    print_warning "Environment file already exists: $ENV_FILE"
fi

# Step 6: Create startup script
print_step "Creating startup script..."

STARTUP_SCRIPT="$SERVER_DIR/start-server.sh"
cat > "$STARTUP_SCRIPT" << EOF
#!/bin/bash
# FindersKeepers v2 MCP Knowledge Server Startup Script

cd "$SERVER_DIR"
source "$VENV_DIR/bin/activate"

# Load environment variables
if [ -f .env ]; then
    export \$(cat .env | grep -v '^#' | xargs)
fi

echo "🚀 Starting FindersKeepers v2 MCP Knowledge Server..."
python src/knowledge_server.py
EOF

chmod +x "$STARTUP_SCRIPT"
print_success "Startup script created: $STARTUP_SCRIPT"

# Step 7: Create Claude Code integration guide
print_step "Creating Claude Code integration guide..."

INTEGRATION_FILE="$SERVER_DIR/CLAUDE_INTEGRATION.md"
cat > "$INTEGRATION_FILE" << EOF
# Claude Code Integration Guide

## Automatic Installation (Recommended)

Add this to your Claude Code \`.claude/settings.local.json\`:

\`\`\`json
{
  "mcpServers": {
    "finderskeepers-knowledge": {
      "command": "$VENV_DIR/bin/python",
      "args": ["$SERVER_DIR/src/knowledge_server.py"],
      "env": {
        "PYTHONPATH": "$SERVER_DIR/src"
      }
    }
  }
}
\`\`\`

## Manual Installation

1. Start the server manually:
\`\`\`bash
$STARTUP_SCRIPT
\`\`\`

2. In Claude Code, connect to the server:
\`\`\`
/mcp connect stdio "$VENV_DIR/bin/python" "$SERVER_DIR/src/knowledge_server.py"
\`\`\`

## Verification

Test the installation by asking Claude:
- "Search our knowledge base for Docker setup"
- "What do we know about session management?"
- "Show me recent project activity"

## Troubleshooting

1. **Database Connection Issues**: Verify services are running:
   \`\`\`bash
   docker-compose ps  # Check if PostgreSQL, Neo4j, Qdrant, Redis are running
   \`\`\`

2. **Environment Variables**: Check your \`.env\` file configuration

3. **Python Dependencies**: Reinstall if needed:
   \`\`\`bash
   $VENV_DIR/bin/pip install -e $SERVER_DIR
   \`\`\`

4. **Logs**: Check server logs for detailed error information

## Configuration

Edit \`$ENV_FILE\` to configure:
- Database connection strings
- API keys for enhanced features  
- Logging levels and formats
- Session management timeouts
EOF

print_success "Integration guide created: $INTEGRATION_FILE"

# Step 8: Run basic verification
print_step "Running installation verification..."

# Test Python imports
if $VENV_DIR/bin/python -c "import asyncpg, neo4j, qdrant_client, redis, httpx, mcp, fastmcp" 2>/dev/null; then
    print_success "All Python dependencies are importable"
else
    print_error "Some Python dependencies failed to import"
    exit 1
fi

# Test server syntax
if $VENV_DIR/bin/python -m py_compile "$SERVER_DIR/src/knowledge_server.py"; then
    print_success "Server syntax validation passed"
else
    print_error "Server syntax validation failed"
    exit 1
fi

# Step 9: Installation summary
echo ""
echo -e "${GREEN}🎉 Installation Complete!${NC}"
echo -e "${BLUE}========================${NC}"
echo ""
echo -e "${YELLOW}📁 Installation Directory:${NC} $SERVER_DIR"
echo -e "${YELLOW}🐍 Virtual Environment:${NC} $VENV_DIR"
echo -e "${YELLOW}⚙️  Configuration File:${NC} $ENV_FILE"
echo -e "${YELLOW}🚀 Startup Script:${NC} $STARTUP_SCRIPT"
echo -e "${YELLOW}📖 Integration Guide:${NC} $INTEGRATION_FILE"
echo ""
echo -e "${PURPLE}Next Steps:${NC}"
echo -e "${BLUE}1.${NC} Edit configuration: ${YELLOW}$ENV_FILE${NC}"
echo -e "${BLUE}2.${NC} Start dependencies: ${YELLOW}docker-compose up -d${NC}"
echo -e "${BLUE}3.${NC} Test server: ${YELLOW}$STARTUP_SCRIPT${NC}"
echo -e "${BLUE}4.${NC} Add to Claude Code: See ${YELLOW}$INTEGRATION_FILE${NC}"
echo ""

# Step 10: Optional quick start
read -p "Would you like to create a quick-start test script? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_step "Creating quick-start test script..."
    
    TEST_SCRIPT="$SERVER_DIR/test-connection.py"
    cat > "$TEST_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""
Quick connection test for FindersKeepers v2 MCP Knowledge Server
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_server():
    """Test basic server functionality"""
    print("🧪 Testing FindersKeepers v2 MCP Knowledge Server")
    print("=" * 50)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from database.postgres_client import PostgresClient
        from database.neo4j_client import Neo4jClient
        from database.qdrant_client import QdrantClient
        from database.redis_client import RedisClient
        print("✅ All imports successful")
        
        # Test database connections (with graceful handling)
        clients = {
            "PostgreSQL": PostgresClient(),
            "Neo4j": Neo4jClient(),
            "Qdrant": QdrantClient(),
            "Redis": RedisClient()
        }
        
        for name, client in clients.items():
            try:
                print(f"🔌 Testing {name} connection...")
                await client.connect()
                health = await client.health_check()
                if health:
                    print(f"✅ {name} connection successful")
                    await client.disconnect()
                else:
                    print(f"⚠️  {name} connection failed health check")
            except Exception as e:
                print(f"❌ {name} connection failed: {e}")
        
        print("\n🎉 Server test completed!")
        print("\nNext: Add to Claude Code settings and start using!")
        
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_server())
EOF

    chmod +x "$TEST_SCRIPT"
    print_success "Test script created: $TEST_SCRIPT"
    
    echo ""
    echo -e "${GREEN}🚀 Ready to test? Run: ${YELLOW}$VENV_DIR/bin/python $TEST_SCRIPT${NC}"
fi

echo ""
echo -e "${GREEN}Installation complete! 🎉${NC}"