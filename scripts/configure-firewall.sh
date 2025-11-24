#!/bin/bash
# Firewall Configuration Script
# Automatically configures firewall based on deployment type

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
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

# Check if .env exists
if [ ! -f .env ]; then
    print_error ".env file not found. Run ./setup.sh first."
    exit 1
fi

# Source environment variables
source .env

print_header "Firewall Configuration"

# Detect firewall tool
if command -v ufw &> /dev/null; then
    FIREWALL="ufw"
elif command -v firewall-cmd &> /dev/null; then
    FIREWALL="firewalld"
else
    print_error "No supported firewall found (ufw or firewalld)"
    echo ""
    echo "Manual configuration required. Open these ports:"
    echo ""
    
    if [[ "$COMPOSE_PROFILES" == *"traefik"* ]]; then
        echo "  - 80/tcp (HTTP)"
        echo "  - 443/tcp (HTTPS)"
    else
        echo "  - ${HTTP_PORT:-5000}/tcp (HTTP)"
    fi
    
    if [[ "$COMPOSE_PROFILES" == *"headscale"* ]]; then
        echo "  - ${HEADSCALE_PORT:-8080}/tcp (Headscale API)"
        echo "  - 41641/udp (WireGuard)"
    fi
    
    exit 1
fi

print_info "Detected firewall: $FIREWALL"
echo ""

# Configure based on firewall type
if [ "$FIREWALL" = "ufw" ]; then
    print_info "Configuring UFW..."
    
    # Check if UFW is active
    if ! sudo ufw status | grep -q "Status: active"; then
        print_info "Enabling UFW..."
        sudo ufw --force enable
    fi
    
    # Allow SSH (important!)
    sudo ufw allow 22/tcp comment 'SSH'
    print_success "Allowed SSH (22/tcp)"
    
    # Configure based on deployment type
    if [[ "$COMPOSE_PROFILES" == *"traefik"* ]]; then
        sudo ufw allow 80/tcp comment 'HTTP'
        print_success "Allowed HTTP (80/tcp)"
        
        sudo ufw allow 443/tcp comment 'HTTPS'
        print_success "Allowed HTTPS (443/tcp)"
    else
        HTTP_PORT=${HTTP_PORT:-5000}
        sudo ufw allow $HTTP_PORT/tcp comment 'Barcode Central HTTP'
        print_success "Allowed HTTP ($HTTP_PORT/tcp)"
    fi
    
    if [[ "$COMPOSE_PROFILES" == *"headscale"* ]]; then
        HEADSCALE_PORT=${HEADSCALE_PORT:-8080}
        sudo ufw allow $HEADSCALE_PORT/tcp comment 'Headscale API'
        print_success "Allowed Headscale API ($HEADSCALE_PORT/tcp)"
        
        sudo ufw allow 41641/udp comment 'WireGuard'
        print_success "Allowed WireGuard (41641/udp)"
    fi
    
    echo ""
    print_info "Current UFW status:"
    sudo ufw status numbered
    
elif [ "$FIREWALL" = "firewalld" ]; then
    print_info "Configuring firewalld..."
    
    # Ensure firewalld is running
    if ! sudo systemctl is-active --quiet firewalld; then
        print_info "Starting firewalld..."
        sudo systemctl start firewalld
        sudo systemctl enable firewalld
    fi
    
    # Allow SSH
    sudo firewall-cmd --permanent --add-service=ssh
    print_success "Allowed SSH"
    
    # Configure based on deployment type
    if [[ "$COMPOSE_PROFILES" == *"traefik"* ]]; then
        sudo firewall-cmd --permanent --add-service=http
        print_success "Allowed HTTP (80/tcp)"
        
        sudo firewall-cmd --permanent --add-service=https
        print_success "Allowed HTTPS (443/tcp)"
    else
        HTTP_PORT=${HTTP_PORT:-5000}
        sudo firewall-cmd --permanent --add-port=$HTTP_PORT/tcp
        print_success "Allowed HTTP ($HTTP_PORT/tcp)"
    fi
    
    if [[ "$COMPOSE_PROFILES" == *"headscale"* ]]; then
        HEADSCALE_PORT=${HEADSCALE_PORT:-8080}
        sudo firewall-cmd --permanent --add-port=$HEADSCALE_PORT/tcp
        print_success "Allowed Headscale API ($HEADSCALE_PORT/tcp)"
        
        sudo firewall-cmd --permanent --add-port=41641/udp
        print_success "Allowed WireGuard (41641/udp)"
    fi
    
    # Reload firewall
    sudo firewall-cmd --reload
    
    echo ""
    print_info "Current firewalld status:"
    sudo firewall-cmd --list-all
fi

echo ""
print_success "Firewall configuration complete!"
echo ""
print_info "Verify connectivity:"

if [[ "$COMPOSE_PROFILES" == *"traefik"* ]]; then
    echo "  curl -I https://$DOMAIN"
else
    echo "  curl -I http://localhost:${HTTP_PORT:-5000}"
fi