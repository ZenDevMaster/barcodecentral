#!/bin/bash
# Fix script for Headscale UI 502 error
# Addresses the "sql: database is closed" and missing user issues

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_header "Fixing Headscale UI 502 Error"
echo ""

# Step 1: Stop all containers to ensure clean state
print_info "Step 1: Stopping containers for clean restart..."
docker compose stop headscale headscale-ui tailscale
sleep 2
print_success "Containers stopped"
echo ""

# Step 2: Start headscale alone and wait for it to be healthy
print_info "Step 2: Starting headscale container..."
docker compose up -d headscale
echo "Waiting for headscale to be healthy (30 seconds)..."
sleep 30

# Check if headscale is running
if ! docker compose ps headscale | grep -q "Up"; then
    print_error "Headscale failed to start!"
    echo "Check logs: docker compose logs headscale"
    exit 1
fi
print_success "Headscale is running"
echo ""

# Step 3: Create a user if it doesn't exist
print_info "Step 3: Creating default user..."
if docker compose exec -T headscale headscale users list 2>/dev/null | grep -q "default"; then
    print_info "User 'default' already exists"
else
    docker compose exec -T headscale headscale users create default
    print_success "Created user 'default'"
fi
echo ""

# Step 4: Generate API key for headscale-ui
print_info "Step 4: Generating API key for Headscale UI..."
API_KEY=$(docker compose exec -T headscale headscale apikeys create 2>/dev/null | grep -oP 'hs_[a-zA-Z0-9]+' | head -1)

if [ -z "$API_KEY" ]; then
    print_error "Failed to generate API key"
    echo "Trying alternative method..."
    API_KEY=$(docker compose exec -T headscale headscale apikeys create --expiration 90d 2>&1 | grep -oP 'hs_[a-zA-Z0-9]+' | head -1)
fi

if [ -n "$API_KEY" ]; then
    print_success "Generated API key: $API_KEY"
    
    # Update .env file
    if grep -q "^HEADSCALE_API_KEY=" .env 2>/dev/null; then
        sed -i "s|^HEADSCALE_API_KEY=.*|HEADSCALE_API_KEY=$API_KEY|" .env
        print_success "Updated HEADSCALE_API_KEY in .env"
    else
        echo "HEADSCALE_API_KEY=$API_KEY" >> .env
        print_success "Added HEADSCALE_API_KEY to .env"
    fi
else
    print_error "Failed to generate API key"
    echo "You'll need to generate it manually:"
    echo "  docker compose exec headscale headscale apikeys create"
    echo "  Then add to .env: HEADSCALE_API_KEY=your-key"
fi
echo ""

# Step 5: Start headscale-ui
print_info "Step 5: Starting headscale-ui..."
docker compose up -d headscale-ui
echo "Waiting for headscale-ui to start (10 seconds)..."
sleep 10
print_success "headscale-ui started"
echo ""

# Step 6: Test connectivity
print_info "Step 6: Testing connectivity..."

# Test if headscale-ui can reach headscale
if docker compose exec -T headscale-ui curl -s -o /dev/null -w "%{http_code}" http://headscale:8080/health 2>/dev/null | grep -q "200"; then
    print_success "headscale-ui CAN reach headscale backend"
else
    print_error "headscale-ui CANNOT reach headscale backend"
fi

# Test if we can reach headscale-ui from host
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3009/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "302" ]; then
    print_success "headscale-ui is responding (HTTP $HTTP_CODE)"
else
    print_error "headscale-ui is NOT responding properly (HTTP $HTTP_CODE)"
fi
echo ""

# Step 7: Start tailscale if needed
if docker compose ps tailscale 2>/dev/null | grep -q "Exit"; then
    print_info "Step 7: Starting tailscale container..."
    docker compose up -d tailscale
    print_success "tailscale started"
else
    print_info "Step 7: tailscale already running or not configured"
fi
echo ""

# Final status
print_header "Status Check"
echo ""
docker compose ps
echo ""

print_header "Next Steps"
echo ""
echo "1. Test the UI in your browser:"
echo "   https://barcode.zendrian.com/headscale-admin/"
echo ""
echo "2. Login credentials (from .env):"
echo "   Username: $(grep HEADSCALE_UI_USER .env | cut -d'=' -f2)"
echo "   Password: $(grep HEADSCALE_UI_PASSWORD .env | cut -d'=' -f2)"
echo ""
echo "3. If still getting 502, check logs:"
echo "   docker compose logs headscale-ui"
echo "   docker compose logs headscale"
echo ""
echo "4. To register the tailscale machine, visit:"
echo "   http://barcode.zendrian.com:8999/register/nodekey:..."
echo "   (Check tailscale logs for the exact URL)"
echo ""

print_success "Fix script completed!"