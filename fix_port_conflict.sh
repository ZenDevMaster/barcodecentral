#!/bin/bash
# Fix port 3000 conflict for headscale-ui

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

echo "=== Fixing Port 3000 Conflict ==="
echo ""

# Check what's using port 3000
print_info "Checking what's using port 3000..."
PORT_USER=$(lsof -i :3000 -t 2>/dev/null || netstat -tlnp 2>/dev/null | grep :3000 | awk '{print $7}' | cut -d'/' -f1 || echo "")

if [ -n "$PORT_USER" ]; then
    print_info "Port 3000 is in use by process: $PORT_USER"
    
    # Check if it's a Docker container
    if docker ps --format '{{.Names}}' | grep -q headscale-ui; then
        print_info "It's the old headscale-ui container"
        print_info "Stopping it..."
        docker stop headscale-ui 2>/dev/null || true
        docker rm headscale-ui 2>/dev/null || true
        print_success "Stopped old container"
    fi
else
    print_info "Port 3000 appears to be free now"
fi

echo ""
print_info "Checking docker-compose.yml port configuration..."

# Check current port mapping in docker-compose.yml
if grep -q "3000:3000" docker-compose.yml; then
    print_info "docker-compose.yml uses port 3000"
    print_info "Your nginx is configured for port 3009"
    echo ""
    echo "Options:"
    echo "1) Change docker-compose.yml to use 3009:3000 (recommended - matches nginx)"
    echo "2) Keep 3000:3000 and update nginx config"
    echo "3) Skip (I'll fix it manually)"
    read -p "Choice [1-3]: " choice
    
    case $choice in
        1)
            print_info "Updating docker-compose.yml to use port 3009..."
            sed -i 's/- "3000:3000"/- "3009:3000"/' docker-compose.yml
            print_success "Updated to port 3009"
            ;;
        2)
            print_info "You'll need to update nginx config to use localhost:3000"
            echo "Edit: /etc/nginx/sites-enabled/barcode-central"
            echo "Change: proxy_pass http://localhost:3009/;"
            echo "To:     proxy_pass http://localhost:3000/;"
            ;;
        3)
            print_info "Skipping port change"
            ;;
    esac
elif grep -q "3009:3000" docker-compose.yml; then
    print_success "docker-compose.yml already uses port 3009 (correct!)"
else
    print_error "Could not find port mapping in docker-compose.yml"
    echo "Please check the file manually"
fi

echo ""
print_info "Restarting containers..."
docker compose up -d

echo ""
print_success "Done! Check status with: docker compose ps"