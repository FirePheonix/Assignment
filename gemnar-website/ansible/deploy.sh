#!/bin/bash
set -e

echo "🚀 Deploying Gemnar Website"
echo "==========================="

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ ERROR: .env file not found at $ENV_FILE"
    echo "Please create a .env file in the project root with GITHUB_TOKEN"
    exit 1
fi

echo "📋 Loading environment variables from .env file..."

# Load environment variables from .env file
set -a  # automatically export all variables
source "$ENV_FILE"
set +a  # stop automatically exporting

# Check if GITHUB_TOKEN is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ ERROR: GITHUB_TOKEN not found in .env file"
    echo "Please add GITHUB_TOKEN=your_token_here to your .env file"
    exit 1
fi

# Validate that the token is not empty
if [ ${#GITHUB_TOKEN} -lt 10 ]; then
    echo "❌ ERROR: GITHUB_TOKEN seems too short (less than 10 characters)"
    echo "Please check your token in the .env file"
    exit 1
fi

# Show token status (masked for security)
echo "✅ GitHub token loaded from .env (${GITHUB_TOKEN:0:4}...${GITHUB_TOKEN: -4})"

# Test GitHub API access
echo "🔍 Testing GitHub API access..."
if curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user > /dev/null 2>&1; then
    echo "✅ GitHub API access successful"
else
    echo "❌ ERROR: Cannot access GitHub API with provided token"
    echo "Please check your token in the .env file"
    exit 1
fi

echo ""
echo "🎯 Starting Ansible deployment..."
echo "================================="

# Change to the ansible directory and run the playbook
cd "$SCRIPT_DIR"
ansible-playbook -i inventory.yml playbook.yml -v

echo ""
echo "✅ Deployment completed successfully!"
echo "🎉 Your website should now be running with WebSocket support!"
echo ""
echo "Next steps:"
echo "1. Test the website: https://gemnar.com"
echo "2. Check WebSocket functionality in chat"
echo "3. Monitor logs: sudo journalctl -u uvicorn -f" 