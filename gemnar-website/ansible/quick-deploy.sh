#!/bin/bash
set -e

echo "🚀 Quick Deploy to Gemnar Server"
echo "================================"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INVENTORY_FILE="$SCRIPT_DIR/inventory.yml"

# Check if inventory file exists
if [ ! -f "$INVENTORY_FILE" ]; then
    echo "❌ ERROR: Inventory file not found at $INVENTORY_FILE"
    exit 1
fi

# Parse inventory.yml to get server credentials
if command -v yq &> /dev/null; then
    # Use yq for proper YAML parsing
    SERVER_IP=$(yq eval '.production.hosts.web.ansible_host' "$INVENTORY_FILE")
    USERNAME=$(yq eval '.production.hosts.web.ansible_user' "$INVENTORY_FILE")
    PASSWORD=$(yq eval '.production.hosts.web.ansible_ssh_pass' "$INVENTORY_FILE")
else
    # Fallback to grep/sed for simple parsing
    echo "ℹ️  yq not found, using grep/sed fallback..."
    SERVER_IP=$(grep -A 10 "ansible_host:" "$INVENTORY_FILE" | grep "ansible_host:" | sed 's/.*ansible_host: *//')
    USERNAME=$(grep -A 10 "ansible_user:" "$INVENTORY_FILE" | grep "ansible_user:" | sed 's/.*ansible_user: *//')
    PASSWORD=$(grep -A 10 "ansible_ssh_pass:" "$INVENTORY_FILE" | grep "ansible_ssh_pass:" | sed 's/.*ansible_ssh_pass: *//')
fi

# Validate extracted values
if [ -z "$SERVER_IP" ] || [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
    echo "❌ ERROR: Could not extract server credentials from inventory file"
    echo "Please check the format of $INVENTORY_FILE"
    exit 1
fi

# Check if sshpass is available
if ! command -v sshpass &> /dev/null; then
    echo "❌ ERROR: sshpass not found. Please install it first:"
    echo "  Ubuntu/Debian: sudo apt-get install sshpass"
    echo "  macOS: brew install sshpass"
    exit 1
fi

echo "📡 Connecting to server: $USERNAME@$SERVER_IP"
echo "🔐 Using credentials from: $INVENTORY_FILE"
echo ""

# SSH connection command prefix with 24-hour keepalive
SSH_CMD="sshpass -p '$PASSWORD' ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=300 -o ServerAliveCountMax=288 -o TCPKeepAlive=yes $USERNAME@$SERVER_IP"

echo "📥 Step 1: Pulling latest changes from git..."
eval "$SSH_CMD 'sudo -u django git -C /home/django/gemnar-website pull origin main'"

echo "📦 Step 2: Installing dependencies with Poetry..."
eval "$SSH_CMD 'cd /home/django/gemnar-website && sudo -u django /home/django/.local/bin/poetry install'"

echo "🗃️  Step 3: Running database migrations..."
eval "$SSH_CMD 'cd /home/django/gemnar-website && sudo -u django ENVIRONMENT=production /home/django/.local/bin/poetry run python manage.py migrate'"

echo "🧹 Step 4: Clearing static files cache..."
eval "$SSH_CMD 'cd /home/django/gemnar-website && sudo -u django rm -rf staticfiles/*'"

echo "📂 Step 5: Collecting static files..."
eval "$SSH_CMD 'cd /home/django/gemnar-website && sudo -u django ENVIRONMENT=production /home/django/.local/bin/poetry run python manage.py collectstatic --noinput --clear'"

echo "🔄 Step 6: Restarting application server..."
eval "$SSH_CMD 'sudo systemctl kill --kill-who=all uvicorn.service || true'"
eval "$SSH_CMD 'sudo systemctl restart uvicorn.service'"

echo ""
echo "✅ Deployment completed successfully!"
echo "🎉 Your website should now be running at: https://gemnar.com"
echo ""
echo "📋 Next steps:"
echo "1. Test the website: https://gemnar.com"
echo "2. Check server status: sudo systemctl status uvicorn.service"
echo "3. Monitor logs: sudo journalctl -u uvicorn -f" 
