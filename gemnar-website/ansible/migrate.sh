#!/bin/bash
set -e

# Gemnar Website Server Migration Script
# =====================================
# This script migrates the Gemnar website from one VPS to another
# by backing up data, deploying to new server, and restoring data.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR" && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
BACKUP_DIR="$PROJECT_ROOT/migration_backup_$(date +%Y%m%d_%H%M%S)"
ANSIBLE_DIR="$PROJECT_ROOT/ansible"

echo -e "${BLUE}🚀 Gemnar Website Server Migration Tool${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to validate prerequisites
validate_prerequisites() {
    print_info "Validating prerequisites..."
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        print_error ".env file not found at $ENV_FILE"
        echo "Please create a .env file with required environment variables."
        exit 1
    fi
    
    # Check if ansible directory exists
    if [ ! -d "$ANSIBLE_DIR" ]; then
        print_error "Ansible directory not found at $ANSIBLE_DIR"
        exit 1
    fi
    
    # Check required commands
    local required_commands=("ansible-playbook" "ssh" "scp" "pg_dump" "curl")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            print_error "Required command '$cmd' not found. Please install it."
            exit 1
        fi
    done
    
    print_status "Prerequisites validated"
}

# Function to load environment variables
load_environment() {
    print_info "Loading environment variables from .env file..."
    
    set -a
    source "$ENV_FILE"
    set +a
    
    # Validate required environment variables
    local required_vars=("GITHUB_TOKEN" "DB_PASSWORD")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            print_error "Required environment variable $var not found in .env file"
            exit 1
        fi
    done
    
    print_status "Environment variables loaded"
}

# Function to backup data from old server
backup_old_server() {
    local old_server="$1"
    
    print_info "Creating backup from old server: $old_server"
    mkdir -p "$BACKUP_DIR"
    
    print_info "Backing up PostgreSQL database..."
    ssh root@"$old_server" "sudo -u postgres pg_dump gemnar_db > /tmp/gemnar_db_backup.sql"
    scp root@"$old_server":/tmp/gemnar_db_backup.sql "$BACKUP_DIR/"
    
    print_info "Backing up media files..."
    scp -r root@"$old_server":/home/django/gemnar-website/media "$BACKUP_DIR/" || print_warning "Media backup failed or no media directory found"
    
    print_info "Backing up logs..."
    scp -r root@"$old_server":/home/django/gemnar-website/logs "$BACKUP_DIR/" || print_warning "Logs backup failed or no logs directory found"
    
    print_info "Backing up SSL certificates..."
    scp -r root@"$old_server":/etc/letsencrypt "$BACKUP_DIR/" || print_warning "SSL certificates backup failed"
    
    print_info "Backing up .env file from server..."
    scp root@"$old_server":/home/django/gemnar-website/.env "$BACKUP_DIR/server.env" || print_warning "Server .env backup failed"
    
    print_status "Backup completed in $BACKUP_DIR"
}

# Function to update inventory for new server
update_inventory() {
    local new_server="$1"
    local inventory_file="$ANSIBLE_DIR/inventory.yml"
    
    print_info "Updating Ansible inventory for new server: $new_server"
    
    # Backup original inventory
    cp "$inventory_file" "$inventory_file.backup"
    
    # Update the ansible_host in inventory
    sed -i "s/ansible_host: .*/ansible_host: $new_server/" "$inventory_file"
    
    print_status "Inventory updated with new server IP"
}

# Function to test SSH connectivity
test_ssh_connection() {
    local server="$1"
    
    print_info "Testing SSH connection to $server..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes root@"$server" "echo 'SSH connection successful'" 2>/dev/null; then
        print_status "SSH connection to $server successful"
    else
        print_error "Cannot connect to $server via SSH"
        echo "Please ensure:"
        echo "1. The server is running and accessible"
        echo "2. SSH key is properly configured"
        echo "3. Root access is available"
        exit 1
    fi
}

# Function to deploy to new server
deploy_to_new_server() {
    print_info "Deploying application to new server..."
    
    cd "$ANSIBLE_DIR"
    
    # Run the main deployment playbook
    if ansible-playbook -i inventory.yml playbook.yml -v; then
        print_status "Application deployed successfully"
    else
        print_error "Deployment failed"
        exit 1
    fi
}

# Function to restore data to new server
restore_data_to_new_server() {
    local new_server="$1"
    
    print_info "Restoring data to new server..."
    
    # Restore database if backup exists
    if [ -f "$BACKUP_DIR/gemnar_db_backup.sql" ]; then
        print_info "Restoring PostgreSQL database..."
        scp "$BACKUP_DIR/gemnar_db_backup.sql" root@"$new_server":/tmp/
        ssh root@"$new_server" "sudo -u postgres psql gemnar_db < /tmp/gemnar_db_backup.sql"
        ssh root@"$new_server" "rm /tmp/gemnar_db_backup.sql"
        print_status "Database restored"
    else
        print_warning "No database backup found, skipping database restore"
    fi
    
    # Restore media files if backup exists
    if [ -d "$BACKUP_DIR/media" ]; then
        print_info "Restoring media files..."
        scp -r "$BACKUP_DIR/media"/* root@"$new_server":/home/django/gemnar-website/media/
        ssh root@"$new_server" "chown -R django:django /home/django/gemnar-website/media"
        print_status "Media files restored"
    else
        print_warning "No media backup found, skipping media restore"
    fi
    
    # Restore SSL certificates if backup exists
    if [ -d "$BACKUP_DIR/letsencrypt" ]; then
        print_info "Restoring SSL certificates..."
        scp -r "$BACKUP_DIR/letsencrypt"/* root@"$new_server":/etc/letsencrypt/
        print_status "SSL certificates restored"
    else
        print_warning "No SSL certificates backup found, they will be regenerated"
    fi
}

# Function to run post-migration tasks
run_post_migration_tasks() {
    local new_server="$1"
    
    print_info "Running post-migration tasks..."
    
    # Run migrations
    print_info "Running Django migrations..."
    cd "$ANSIBLE_DIR"
    ansible-playbook -i inventory.yml migrate.yml -v
    
    # Restart services
    print_info "Restarting services..."
    ssh root@"$new_server" "systemctl restart uvicorn nginx postgresql"
    
    # Wait for services to start
    sleep 10
    
    # Test the website
    print_info "Testing website connectivity..."
    if curl -s -o /dev/null -w "%{http_code}" "https://gemnar.com" | grep -q "200\|301\|302"; then
        print_status "Website is responding"
    else
        print_warning "Website may not be responding correctly"
    fi
    
    print_status "Post-migration tasks completed"
}

# Function to update DNS (manual step)
show_dns_instructions() {
    local new_server="$1"
    
    echo ""
    print_info "DNS Update Instructions:"
    echo "=================================================="
    echo "1. Update your DNS records to point to the new server:"
    echo "   - A record for gemnar.com -> $new_server"
    echo "   - A record for www.gemnar.com -> $new_server"
    echo ""
    echo "2. Wait for DNS propagation (can take up to 24 hours)"
    echo ""
    echo "3. Once DNS has propagated, you may want to:"
    echo "   - Update the ALLOWED_HOSTS in .env if needed"
    echo "   - Regenerate SSL certificates if they weren't restored"
    echo "   - Monitor logs: ssh root@$new_server 'journalctl -u uvicorn -f'"
    echo ""
}

# Function to show rollback instructions
show_rollback_instructions() {
    local old_server="$1"
    
    echo ""
    print_warning "Rollback Instructions (if needed):"
    echo "=================================================="
    echo "1. Update DNS records back to old server: $old_server"
    echo "2. Restore original inventory: cp $ANSIBLE_DIR/inventory.yml.backup $ANSIBLE_DIR/inventory.yml"
    echo "3. The old server should still be running with the previous setup"
    echo ""
}

# Main migration function
migrate_server() {
    local old_server="$1"
    local new_server="$2"
    
    echo ""
    print_info "Migration Summary:"
    echo "Old Server: $old_server"
    echo "New Server: $new_server"
    echo "Backup Directory: $BACKUP_DIR"
    echo ""
    
    read -p "Do you want to continue with the migration? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Migration cancelled"
        exit 0
    fi
    
    # Step 1: Validate prerequisites
    validate_prerequisites
    
    # Step 2: Load environment
    load_environment
    
    # Step 3: Test connections
    test_ssh_connection "$old_server"
    test_ssh_connection "$new_server"
    
    # Step 4: Backup old server
    backup_old_server "$old_server"
    
    # Step 5: Update inventory
    update_inventory "$new_server"
    
    # Step 6: Deploy to new server
    deploy_to_new_server
    
    # Step 7: Restore data
    restore_data_to_new_server "$new_server"
    
    # Step 8: Post-migration tasks
    run_post_migration_tasks "$new_server"
    
    # Step 9: Show manual steps
    show_dns_instructions "$new_server"
    show_rollback_instructions "$old_server"
    
    print_status "Migration completed successfully!"
    echo ""
    print_info "Next steps:"
    echo "1. Update DNS records as shown above"
    echo "2. Monitor the new server for any issues"
    echo "3. Keep the old server running until DNS propagation is complete"
    echo "4. Test all functionality on the new server"
    echo ""
}

# Usage function
show_usage() {
    echo "Usage: $0 <old_server_ip> <new_server_ip>"
    echo ""
    echo "Example: $0 45.77.103.30 192.168.1.100"
    echo ""
    echo "This script will:"
    echo "1. Backup data from the old server"
    echo "2. Deploy the application to the new server"
    echo "3. Restore data to the new server"
    echo "4. Provide instructions for DNS updates"
    echo ""
    echo "Prerequisites:"
    echo "- SSH key access to both servers as root"
    echo "- .env file with GITHUB_TOKEN and other required variables"
    echo "- Ansible installed locally"
    echo ""
}

# Backup only function
backup_only() {
    local server="$1"
    
    print_info "Backup-only mode for server: $server"
    
    validate_prerequisites
    load_environment
    test_ssh_connection "$server"
    backup_old_server "$server"
    
    print_status "Backup completed in $BACKUP_DIR"
}

# Main script logic
case "${1:-}" in
    "backup")
        if [ -z "$2" ]; then
            print_error "Server IP required for backup mode"
            echo "Usage: $0 backup <server_ip>"
            exit 1
        fi
        backup_only "$2"
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    "")
        show_usage
        ;;
    *)
        if [ -z "$2" ]; then
            print_error "Both old and new server IPs are required"
            show_usage
            exit 1
        fi
        migrate_server "$1" "$2"
        ;;
esac