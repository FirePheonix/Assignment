#!/bin/bash

# This script reboots the production server by reading credentials from ansible/inventory.yml

# Function to parse YAML file
get_yaml_value() {
    grep "$1" ansible/inventory.yml | awk '{print $2}'
}

# Get credentials from inventory file
HOST=$(get_yaml_value ansible_host)
USER=$(get_yaml_value ansible_user)
PASSWORD=$(get_yaml_value ansible_ssh_pass)

# Check if credentials were found
if [ -z "$HOST" ] || [ -z "$USER" ] || [ -z "$PASSWORD" ]; then
    echo "Error: Could not parse server details from ansible/inventory.yml"
    exit 1
fi

# Use sshpass to execute the reboot command
echo "Rebooting server at $HOST..."
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=300 -o ServerAliveCountMax=288 -o TCPKeepAlive=yes "${USER}@${HOST}" 'sudo reboot'

echo "Reboot command sent." 