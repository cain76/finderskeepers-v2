#!/bin/bash
# FindersKeepers v2 - Environment Setup Helper
# Copies credentials from Bitcain .env and creates FindersKeepers v2 .env file

set -e

BITCAIN_ENV="/media/cain/linux_storage/bitcain/.env"
FK2_ENV=".env"
FK2_ENV_EXAMPLE=".env.example"

echo "🔧 Setting up FindersKeepers v2 environment..."

# Check if bitcain .env exists
if [ ! -f "$BITCAIN_ENV" ]; then
    echo "❌ Bitcain .env file not found at $BITCAIN_ENV"
    echo "Please ensure Bitcoin project .env file exists first"
    exit 1
fi

# Check if .env.example exists
if [ ! -f "$FK2_ENV_EXAMPLE" ]; then
    echo "❌ .env.example not found! Please ensure you're in the FindersKeepers v2 directory"
    exit 1
fi

# Backup existing .env if it exists
if [ -f "$FK2_ENV" ]; then
    echo "📋 Backing up existing .env to .env.backup"
    cp "$FK2_ENV" ".env.backup"
fi

# Start with the example template
echo "📝 Creating new .env from template..."
cp "$FK2_ENV_EXAMPLE" "$FK2_ENV"

# Extract credentials from Bitcain .env
echo "🔑 Extracting credentials from Bitcain project..."

# Docker credentials
DOCKER_USERNAME=$(grep "^DOCKER_USERNAME=" "$BITCAIN_ENV" | cut -d'=' -f2- | tr -d '"')
DOCKER_TOKEN=$(grep "^DOCKER_TOKEN=" "$BITCAIN_ENV" | cut -d'=' -f2- | tr -d '"')

# AI API Keys
OPENAI_API_KEY=$(grep "^OPENAI_API_KEY=" "$BITCAIN_ENV" | cut -d'=' -f2- | tr -d '"')
GOOGLE_API_KEY=$(grep "^GOOGLE_API_KEY=" "$BITCAIN_ENV" | cut -d'=' -f2- | tr -d '"')
ANTHROPIC_API_KEY=$(grep "^ANTHROPIC_API_KEY=" "$BITCAIN_ENV" | cut -d'=' -f2- | tr -d '"')
PERPLEXITY_API_KEY=$(grep "^PERPLEXITY_API_KEY=" "$BITCAIN_ENV" | cut -d'=' -f2- | tr -d '"')
TAVILY_API_KEY=$(grep "^TAVILY_API_KEY=" "$BITCAIN_ENV" | cut -d'=' -f2- | tr -d '"')

# GitHub credentials
GITHUB_TOKEN=$(grep "^GITHUB_PERSONAL_ACCESS_TOKEN=" "$BITCAIN_ENV" | cut -d'=' -f2- | tr -d '"')

# Update .env file with actual values
echo "✏️  Updating .env with extracted credentials..."

# Docker credentials
if [ -n "$DOCKER_USERNAME" ]; then
    sed -i "s|DOCKER_USERNAME=.*|DOCKER_USERNAME=$DOCKER_USERNAME|" "$FK2_ENV"
    echo "✅ Docker username configured"
fi

if [ -n "$DOCKER_TOKEN" ]; then
    sed -i "s|DOCKER_TOKEN=.*|DOCKER_TOKEN=$DOCKER_TOKEN|" "$FK2_ENV"
    echo "✅ Docker token configured"
fi

# AI API Keys
if [ -n "$OPENAI_API_KEY" ]; then
    sed -i "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=$OPENAI_API_KEY|" "$FK2_ENV"
    echo "✅ OpenAI API key configured"
fi

if [ -n "$GOOGLE_API_KEY" ]; then
    sed -i "s|GOOGLE_API_KEY=.*|GOOGLE_API_KEY=$GOOGLE_API_KEY|" "$FK2_ENV"
    echo "✅ Google API key configured"
fi

if [ -n "$ANTHROPIC_API_KEY" ]; then
    sed -i "s|ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY|" "$FK2_ENV"
    echo "✅ Anthropic API key configured"
fi

if [ -n "$PERPLEXITY_API_KEY" ]; then
    sed -i "s|PERPLEXITY_API_KEY=.*|PERPLEXITY_API_KEY=$PERPLEXITY_API_KEY|" "$FK2_ENV"
    echo "✅ Perplexity API key configured"
fi

if [ -n "$TAVILY_API_KEY" ]; then
    sed -i "s|TAVILY_API_KEY=.*|TAVILY_API_KEY=$TAVILY_API_KEY|" "$FK2_ENV"
    echo "✅ Tavily API key configured"
fi

if [ -n "$GITHUB_TOKEN" ]; then
    sed -i "s|GITHUB_TOKEN=.*|GITHUB_TOKEN=$GITHUB_TOKEN|" "$FK2_ENV"
    echo "✅ GitHub token configured"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Environment setup complete!"
echo ""
echo "✅ Credentials copied from: $BITCAIN_ENV"
echo "✅ New .env file created: $FK2_ENV"
echo ""
echo "Next steps:"
echo "1. Review .env file for any additional customizations"
echo "2. Run: ./scripts/start-all.sh"
echo ""
echo "Note: .env file contains sensitive information - do not commit to git!"