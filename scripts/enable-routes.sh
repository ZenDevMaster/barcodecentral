#!/bin/bash
# Enable Headscale Subnet Routes
# Run this after setting up Raspberry Pi print servers

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Headscale is running
if ! docker ps | grep -q headscale; then
    print_error "Headscale container is not running"
    echo "Start it with: docker compose up -d"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Headscale Route Management"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# List all routes (Headscale v0.27+ syntax: nodes list-routes)
print_info "Current routes:"
echo ""
docker exec headscale headscale nodes list-routes

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if there are any routes to enable
# Strip any whitespace/newlines from the count
PENDING_ROUTES=$(docker exec headscale headscale nodes list-routes 2>/dev/null | grep -c "false" | tr -d '\n' || echo "0")

if [ "$PENDING_ROUTES" -eq 0 ] 2>/dev/null; then
    print_success "No pending routes to enable"
    echo ""
    print_info "All routes are already enabled or no routes advertised yet"
    echo ""
    echo "To advertise routes from Raspberry Pi:"
    echo "  1. Ensure Tailscale is running on the Pi"
    echo "  2. Check: sudo tailscale status"
    echo "  3. Routes should appear here within a few minutes"
    exit 0
fi

print_warning "Found $PENDING_ROUTES pending route(s)"
echo ""

# Interactive mode
while true; do
    echo "Options:"
    echo "  1) Enable all pending routes"
    echo "  2) Enable specific route by ID"
    echo "  3) List routes again"
    echo "  4) Exit"
    echo ""
    read -p "Select option [1-4]: " choice
    
    case $choice in
        1)
            print_info "Enabling all pending routes..."
            echo ""
            
            # Get all route IDs that are not enabled
            ROUTE_IDS=$(docker exec headscale headscale nodes list-routes 2>/dev/null | grep "false" | awk '{print $1}' || echo "")

            if [ -z "$ROUTE_IDS" ]; then
                print_warning "No routes to enable"
            else
                for ROUTE_ID in $ROUTE_IDS; do
                    # Headscale v0.27+ syntax: nodes approve-routes -r <id>
                    if docker exec headscale headscale nodes approve-routes -r "$ROUTE_ID" 2>/dev/null; then
                        print_success "Enabled route $ROUTE_ID"
                    else
                        print_error "Failed to enable route $ROUTE_ID"
                    fi
                done
            fi
            
            echo ""
            print_info "Updated routes:"
            docker exec headscale headscale nodes list-routes
            echo ""
            ;;
            
        2)
            read -p "Enter route ID to enable: " ROUTE_ID
            
            if [ -z "$ROUTE_ID" ]; then
                print_error "Route ID cannot be empty"
                continue
            fi
            
            # Headscale v0.27+ syntax: nodes approve-routes
            if docker exec headscale headscale nodes approve-routes -r "$ROUTE_ID" 2>/dev/null; then
                print_success "Enabled route $ROUTE_ID"
            else
                print_error "Failed to enable route $ROUTE_ID"
            fi
            
            echo ""
            ;;
            
        3)
            echo ""
            docker exec headscale headscale nodes list-routes
            echo ""
            ;;
            
        4)
            print_info "Exiting..."
            exit 0
            ;;
            
        *)
            print_error "Invalid option"
            ;;
    esac
done