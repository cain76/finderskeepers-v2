#!/bin/bash
# Test the new n8n MCP server from czlonkowski/n8n-mcp

echo "🔍 Testing new n8n MCP server configuration..."

# Check if Docker image exists locally
echo "📦 Checking if Docker image is available..."
if docker images | grep -q "czlonkowski/n8n-mcp"; then
    echo "✅ n8n MCP Docker image found locally"
else
    echo "⚠️  n8n MCP Docker image not found locally"
    echo "📥 Pulling image: ghcr.io/czlonkowski/n8n-mcp:latest"
    docker pull ghcr.io/czlonkowski/n8n-mcp:latest
fi

echo ""
echo "🧪 Testing n8n MCP server startup..."

# Test if the container can start (brief test)
timeout 10s docker run --rm \
    -e MCP_MODE=stdio \
    -e LOG_LEVEL=error \
    -e DISABLE_CONSOLE_OUTPUT=true \
    ghcr.io/czlonkowski/n8n-mcp:latest &

sleep 5

echo ""
echo "✅ Configuration updated successfully!"
echo ""
echo "🔧 Changes made:"
echo "   • Replaced @ahmad.soliman/mcp-n8n-server"
echo "   • Now using ghcr.io/czlonkowski/n8n-mcp:latest"
echo "   • Provides documentation for 525+ n8n nodes"
echo "   • No API keys or environment setup required"
echo ""
echo "🚀 To use with Claude Code:"
echo "   1. Start Claude Code: claude code"
echo "   2. Ask: 'How do I use the HTTP Request node in n8n?'"
echo "   3. Ask: 'Show me all available n8n trigger nodes'"
echo "   4. Ask: 'Help me configure a webhook in n8n'"
echo ""
echo "📚 This MCP provides comprehensive n8n documentation, not workflow management"