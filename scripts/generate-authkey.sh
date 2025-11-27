#!/bin/bash
# Generate Headscale Pre-Auth Key
# Use this key when setting up Raspberry Pi print servers

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if Headscale is running
if ! docker ps | grep -q headscale; then
    echo "Error: Headscale container is not running"
    echo "Start it with: docker compose up -d"
    exit 1
fi

echo "Generating Headscale Pre-Auth Key..."
echo ""

# Create user if it doesn't exist
docker exec headscale headscale users create barcode-central 2>/dev/null || true

# Get the user ID for barcode-central (Headscale v0.27+ requires numeric ID)
# Strip ANSI color codes from output using sed
USER_ID=$(docker exec headscale headscale users list 2>/dev/null | grep barcode-central | awk '{print $1}' | sed 's/\x1b\[[0-9;]*m//g' | tr -d '[:space:]')

if [ -z "$USER_ID" ]; then
    echo "Error: Could not find user 'barcode-central'"
    echo "Check Headscale users: docker exec headscale headscale users list"
    exit 1
fi

# Generate pre-auth key (Headscale v0.27+ syntax)
# Command format: headscale preauthkeys create -e 90d -u <USER_ID> --reusable
AUTHKEY=$(docker exec headscale headscale preauthkeys create -e 90d -u "$USER_ID" --reusable 2>&1 | tail -1 | tr -d '[:space:]')

if [ -z "$AUTHKEY" ] || [ ${#AUTHKEY} -lt 20 ]; then
    echo "Error: Failed to generate auth key"
    echo "Check Headscale logs: docker compose logs headscale"
    exit 1
fi

echo ""
print_success "Pre-Auth Key Generated!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$AUTHKEY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_info "This key is valid for 90 days and can be reused"
echo ""
echo "Use this key when setting up Raspberry Pi print servers:"
echo "  1. Run: curl -sSL https://raw.githubusercontent.com/ZenDevMaster/barcodecentral/main/raspberry-pi-setup.sh | bash"
echo "  2. Or manually: ./raspberry-pi-setup.sh"
echo "  3. Enter this key when prompted"
echo ""
print_warning "Save this key securely - you'll need it for each Raspberry Pi"
echo ""

# Optionally update .env file
if [ -f .env ]; then
    if grep -q "TAILSCALE_AUTHKEY=" .env; then
        print_info "Updating .env file..."
        sed -i "s|^TAILSCALE_AUTHKEY=.*|TAILSCALE_AUTHKEY=$AUTHKEY|" .env
        print_success "Updated TAILSCALE_AUTHKEY in .env"
    else
        echo "TAILSCALE_AUTHKEY=$AUTHKEY" >> .env
        print_success "Added TAILSCALE_AUTHKEY to .env"
    fi
    echo ""
    print_info "Restart application to use new key: docker compose restart app tailscale"
fi