#!/bin/bash

# SSH connection script for Gemnar production server
# Reads credentials from ansible/inventory.yml

SCRIPT_DIR="$(dirname "$0")"
INVENTORY_FILE="$SCRIPT_DIR/inventory.yml"

if [ ! -f "$INVENTORY_FILE" ]; then
    echo "Error: Inventory file not found at $INVENTORY_FILE"
    exit 1
fi

# Parse inventory.yml using yq or fallback to grep/sed
if command -v yq &> /dev/null; then
    # Use yq for proper YAML parsing
    SERVER_IP=$(yq eval '.production.hosts.web.ansible_host' "$INVENTORY_FILE")
    USERNAME=$(yq eval '.production.hosts.web.ansible_user' "$INVENTORY_FILE")
    PASSWORD=$(yq eval '.production.hosts.web.ansible_ssh_pass' "$INVENTORY_FILE")
else
    # Fallback to grep/sed for simple parsing
    echo "yq not found, using grep/sed fallback..."
    SERVER_IP=$(grep -A 10 "ansible_host:" "$INVENTORY_FILE" | grep "ansible_host:" | sed 's/.*ansible_host: *//')
    USERNAME=$(grep -A 10 "ansible_user:" "$INVENTORY_FILE" | grep "ansible_user:" | sed 's/.*ansible_user: *//')
    PASSWORD=$(grep -A 10 "ansible_ssh_pass:" "$INVENTORY_FILE" | grep "ansible_ssh_pass:" | sed 's/.*ansible_ssh_pass: *//')
fi

# Validate extracted values
if [ -z "$SERVER_IP" ] || [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
    echo "Error: Could not extract server credentials from inventory file"
    echo "Please check the format of $INVENTORY_FILE"
    exit 1
fi

echo "Connecting to Gemnar production server..."
echo "Server: $USERNAME@$SERVER_IP"
echo "Reading credentials from: $INVENTORY_FILE"
echo ""

# Use sshpass for password authentication
if command -v sshpass &> /dev/null; then
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=300 -o ServerAliveCountMax=288 -o TCPKeepAlive=yes "$USERNAME@$SERVER_IP"
else
    echo "sshpass not found. Please install it first:"
    echo "  Ubuntu/Debian: sudo apt-get install sshpass"
    echo "  macOS: brew install sshpass"
    echo "  Or manually connect with: ssh $USERNAME@$SERVER_IP"
    echo "  Password: $PASSWORD"
fi 